"""
API Routes
"""
import os
import time
import logging
import shutil
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.schemas import (
    QueryRequest, QueryResponse, IngestResponse,
    RetrievedChunk, EscalationStatus, QueryIntent, HumanResponseRequest
)
from app.core.document_processor import DocumentProcessor
from app.core.vector_store import vector_store
from app.graph.workflow import support_graph
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session store (use Redis in production)
session_store: dict = {}
pending_escalations: dict = {}


# ─────────────────────────────────────────────
# DOCUMENT INGESTION
# ─────────────────────────────────────────────

@router.post("/ingest", response_model=IngestResponse, tags=["Document Ingestion"])
async def ingest_document(file: UploadFile = File(...)):
    """
    Upload and ingest a PDF into the RAG knowledge base.
    Pipeline: PDF Upload → Text Extraction → Chunking → Embedding → ChromaDB Storage
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        # Save uploaded file temporarily
        upload_dir = "./data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Process document
        processor = DocumentProcessor(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        chunks = processor.process_pdf(file_path)

        # Initialize vector store and add documents
        vector_store.initialize()
        chunks_added = vector_store.add_documents(chunks)

        logger.info(f"Ingested {file.filename}: {chunks_added} chunks created")

        return IngestResponse(
            status="success",
            chunks_created=chunks_added,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            message=f"Successfully processed '{file.filename}' and created {chunks_added} searchable chunks."
        )

    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


# ─────────────────────────────────────────────
# QUERY PROCESSING
# ─────────────────────────────────────────────

@router.post("/query", response_model=QueryResponse, tags=["Query"])
async def process_query(request: QueryRequest):
    """
    Process a customer support query through the LangGraph RAG pipeline.

    Flow:
      Intent Detection → Retrieval → Confidence Check → Response Generation / HITL
    """
    start_time = time.time()

    try:
        # Restore session history
        history = session_store.get(request.session_id, [])

        # Initialize graph state
        initial_state = {
            "session_id": request.session_id,
            "query": request.query,
            "conversation_history": history,
            "intent": None,
            "retrieved_chunks": [],
            "confidence": 0.0,
            "answer": None,
            "is_escalated": False,
            "escalation_reason": None,
            "escalation_status": "none",
            "human_response": None,
            "error": None,
            "processing_start": start_time
        }

        # Use LangGraph workflow for proper HITL handling
        final_state = support_graph.invoke({
            "session_id": request.session_id,
            "query": request.query,
            "conversation_history": history,
            "intent": None,
            "retrieved_chunks": [],
            "confidence": 0.0,
            "answer": None,
            "is_escalated": False,
            "escalation_reason": None,
            "escalation_status": "none",
            "human_response": None,
            "error": None,
            "processing_start": start_time
        })

        # Update session history
        history.append({"role": "user", "content": request.query})
        history.append({"role": "assistant", "content": final_state.get("answer", "")})
        session_store[request.session_id] = history[-10:]  # Keep last 5 turns

        # Store escalation if needed
        if final_state.get("is_escalated"):
            pending_escalations[request.session_id] = {
                "query": request.query,
                "reason": final_state.get("escalation_reason"),
                "timestamp": datetime.now().isoformat()
            }

        elapsed_ms = (time.time() - start_time) * 1000

        # Build response
        chunks = [
            RetrievedChunk(
                content=c["content"],
                source=c["source"],
                relevance_score=c["relevance_score"],
                chunk_id=c["chunk_id"]
            )
            for c in final_state.get("retrieved_chunks", [])
        ]

        intent_value = final_state.get("intent", "general")
        try:
            intent = QueryIntent(intent_value)
        except ValueError:
            intent = QueryIntent.GENERAL

        escalation_status_value = final_state.get("escalation_status", "none")
        try:
            esc_status = EscalationStatus(escalation_status_value)
        except ValueError:
            esc_status = EscalationStatus.NONE

        return QueryResponse(
            session_id=request.session_id,
            query=request.query,
            answer=final_state.get("answer", "Unable to generate response"),
            intent=intent,
            confidence=round(final_state.get("confidence", 0.0), 4),
            retrieved_chunks=chunks,
            is_escalated=final_state.get("is_escalated", False),
            escalation_status=esc_status,
            escalation_reason=final_state.get("escalation_reason"),
            human_response=final_state.get("human_response"),
            timestamp=datetime.now(),
            processing_time_ms=round(elapsed_ms, 2)
        )

    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


# ─────────────────────────────────────────────
# HITL MANAGEMENT
# ─────────────────────────────────────────────

@router.get("/escalations", tags=["HITL"])
async def get_pending_escalations():
    """Get all pending HITL escalations for the agent dashboard"""
    return {
        "total": len(pending_escalations),
        "escalations": [
            {"session_id": sid, **data}
            for sid, data in pending_escalations.items()
        ]
    }


@router.post("/escalations/respond", tags=["HITL"])
async def respond_to_escalation(request: HumanResponseRequest):
    """Human agent responds to an escalated query"""
    if request.session_id not in pending_escalations:
        raise HTTPException(status_code=404, detail="Escalation not found")

    escalation = pending_escalations.pop(request.session_id)
    return {
        "status": "resolved",
        "session_id": request.session_id,
        "agent": request.agent_name,
        "response": request.human_agent_response,
        "original_query": escalation["query"],
        "resolved_at": datetime.now().isoformat()
    }


# ─────────────────────────────────────────────
# SYSTEM INFO
# ─────────────────────────────────────────────

@router.get("/stats", tags=["System"])
async def get_system_stats():
    """Get system statistics"""
    try:
        stats = vector_store.get_collection_stats()
    except:
        stats = {"count": 0, "initialized": False}

    return {
        "vector_store": stats,
        "active_sessions": len(session_store),
        "pending_escalations": len(pending_escalations),
        "model": settings.OPENAI_MODEL,
        "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
        "chunk_size": settings.CHUNK_SIZE,
        "top_k": settings.TOP_K_RESULTS,
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD
    }


@router.delete("/session/{session_id}", tags=["System"])
async def clear_session(session_id: str):
    """Clear a conversation session"""
    session_store.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}
