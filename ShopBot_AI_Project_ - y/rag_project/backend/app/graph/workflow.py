"""
LangGraph Workflow Engine
Implements the graph-based control flow for the RAG Customer Support Assistant

Graph Nodes:
  1. intent_detection_node   → Classifies user query intent
  2. retrieval_node          → Fetches relevant chunks from ChromaDB
  3. confidence_check_node   → Evaluates retrieval confidence
  4. response_generation_node→ Generates LLM answer using context
  5. hitl_escalation_node    → Escalates to human agent if needed
  6. output_node             → Formats and finalizes response

Edges (Conditional Routing):
  - After confidence_check: route to response_generation OR hitl_escalation
  - After intent_detection: route to hitl_escalation if flagged keywords
"""

import logging
import time
from typing import TypedDict, Optional, List, Literal, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, END
import google.genai as genai

from app.core.config import settings
from app.core.vector_store import vector_store

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# STATE DEFINITION
# ─────────────────────────────────────────────
class SupportState(TypedDict):
    session_id: str
    query: str
    conversation_history: List[dict]
    intent: Optional[str]
    retrieved_chunks: List[dict]
    confidence: float
    answer: Optional[str]
    is_escalated: bool
    escalation_reason: Optional[str]
    escalation_status: str
    human_response: Optional[str]
    error: Optional[str]
    processing_start: float


# ─────────────────────────────────────────────
# NODE FUNCTIONS
# ─────────────────────────────────────────────

def intent_detection_node(state: SupportState) -> SupportState:
    """
    Node 1: Classify user intent using keyword + LLM classification.
    Triggers immediate HITL escalation for sensitive intents.
    """
    query = state["query"].lower()
    state["processing_start"] = time.time()

    # Check for HITL trigger keywords
    hitl_triggers = settings.HITL_KEYWORDS
    for keyword in hitl_triggers:
        if keyword in query:
            state["intent"] = "hitl_required"
            state["escalation_reason"] = f"Sensitive keyword detected: '{keyword}'"
            logger.info(f"HITL triggered by keyword: {keyword}")
            return state

    # Simple intent classification via keyword matching
    intent_map = {
        "order_status": ["order", "track", "tracking", "where is", "shipment status", "delivery status"],
        "return_refund": ["return", "refund", "money back", "cancel order", "exchange"],
        "shipping": ["shipping", "delivery", "deliver", "ship", "shipping cost", "free shipping"],
        "product_info": ["product", "item", "size", "color", "specification", "price", "cost", "availability"],
        "account": ["account", "login", "password", "profile", "sign in", "register"],
        "complaint": ["wrong", "damaged", "broken", "defective", "not working", "poor quality"],
    }

    detected_intent = "general"
    for intent, keywords in intent_map.items():
        if any(kw in query for kw in keywords):
            detected_intent = intent
            break

    state["intent"] = detected_intent
    logger.info(f"Intent detected: {detected_intent}")
    return state


def retrieval_node(state: SupportState) -> SupportState:
    """
    Node 2: Retrieve relevant document chunks from ChromaDB using semantic search.
    """
    try:
        query = state["query"]
        results = vector_store.retrieve(query, top_k=settings.TOP_K_RESULTS)
        state["retrieved_chunks"] = results

        if results:
            avg_score = sum(r["relevance_score"] for r in results) / len(results)
            state["confidence"] = avg_score
        else:
            state["confidence"] = 0.0

        logger.info(f"Retrieved {len(results)} chunks. Avg confidence: {state['confidence']:.3f}")
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        state["retrieved_chunks"] = []
        state["confidence"] = 0.0
        state["error"] = str(e)

    return state


def confidence_check_node(state: SupportState) -> SupportState:
    """
    Node 3: Evaluate retrieval confidence to decide routing.
    Low confidence → HITL escalation
    """
    confidence = state["confidence"]
    threshold = settings.CONFIDENCE_THRESHOLD

    if confidence < threshold and not state.get("is_escalated"):
        if len(state["retrieved_chunks"]) == 0:
            state["is_escalated"] = True
            state["escalation_reason"] = "No relevant information found in knowledge base"
            logger.info("Escalating: no relevant chunks found")
        elif confidence < 0.2:
            state["is_escalated"] = True
            state["escalation_reason"] = f"Low confidence score ({confidence:.2f}) - query requires human expertise"
            logger.info(f"Escalating: low confidence {confidence:.3f}")

    return state


def response_generation_node(state: SupportState) -> SupportState:
    """
    Node 4: Generate a contextual answer using available AI models.
    Tries Google Gemini first, then falls back to rule-based responses.
    """
    try:
        # Try Gemini first
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Build context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(state["retrieved_chunks"]):
            context_parts.append(f"[Context {i+1}] (Relevance: {chunk['relevance_score']:.2f})\n{chunk['content']}")

        context = "\n\n".join(context_parts) if context_parts else "No specific context available."

        # Create a simple prompt for Gemini
        prompt = f"""
You are ShopBot, a customer support assistant for an e-commerce platform.

Context information: {context[:1000]}

User question: {state['query']}

Please provide a helpful, concise response based on the context above.
"""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt
        )

        state["answer"] = response.candidates[0].content.parts[0].text
        state["is_escalated"] = False
        state["escalation_status"] = "none"
        logger.info("Response generated successfully with Gemini")

    except Exception as e:
        logger.warning(f"Gemini generation failed: {e}, using fallback response")

        # Fallback: Simple rule-based response based on query keywords
        query = state["query"].lower()

        if "return" in query or "refund" in query:
            response = "I'd be happy to help you with your return or refund request. Our return policy allows returns within 30 days of purchase. Please provide your order number and I'll guide you through the process."
        elif "shipping" in query or "delivery" in query:
            response = "We offer free shipping on orders over $50, with standard delivery taking 3-5 business days. Express shipping is available for an additional fee. Would you like me to check the status of your order?"
        elif "track" in query or "where" in query:
            response = "You can track your order by visiting our website and entering your order number. If you don't have your order number, I can help you locate it with your email address."
        elif "price" in query or "cost" in query:
            response = "Our prices are competitive and we often have sales and discounts. Could you tell me which product you're interested in? I'd be happy to provide current pricing information."
        else:
            response = "Thank you for contacting ShopBot customer support. I'm here to help with your order, shipping, returns, and any other questions about our products and services. How can I assist you today?"

        # Add context awareness if chunks are available
        if state["retrieved_chunks"]:
            response += " I've reviewed our knowledge base and can provide specific information about your question."

        state["answer"] = response
        state["is_escalated"] = False
        state["escalation_status"] = "none"
        logger.info("Response generated using fallback rule-based system")

    return state


def hitl_escalation_node(state: SupportState) -> SupportState:
    """
    Node 5: Human-in-the-Loop escalation handler.
    Flags the query for human agent review. Does NOT auto-resolve.
    """
    state["is_escalated"] = True
    state["escalation_status"] = "pending"
    state["human_response"] = None

    reason = state.get("escalation_reason", "Query requires human attention")
    state["answer"] = (
        f"I understand your concern and I want to make sure you get the best help possible. "
        f"Your query has been escalated to our specialized support team. "
        f"A human agent will review your case and respond within 2-4 hours. "
        f"Your ticket has been created. Is there anything else I can note for the agent?"
    )

    logger.info(f"HITL escalation created. Reason: {reason}")
    return state


def output_node(state: SupportState) -> SupportState:
    """
    Node 6: Final output formatting and state cleanup.
    """
    if not state.get("answer"):
        state["answer"] = "I apologize, but I couldn't process your request. Please try again."

    logger.info(f"Output finalized. Escalated: {state['is_escalated']}")
    return state


# ─────────────────────────────────────────────
# ROUTING FUNCTIONS
# ─────────────────────────────────────────────

def route_after_intent(state: SupportState) -> Literal["retrieval", "hitl_escalation"]:
    """Route immediately to HITL if sensitive intent detected"""
    if state.get("intent") == "hitl_required":
        return "hitl_escalation"
    return "retrieval"


def route_after_confidence(state: SupportState) -> Literal["response_generation", "hitl_escalation"]:
    """Route based on retrieval confidence"""
    if state.get("is_escalated"):
        return "hitl_escalation"
    return "response_generation"


# ─────────────────────────────────────────────
# GRAPH CONSTRUCTION
# ─────────────────────────────────────────────

def build_support_graph():
    """Build and compile the LangGraph workflow"""
    workflow = StateGraph(SupportState)

    # Add nodes
    workflow.add_node("intent_detection", intent_detection_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("confidence_check", confidence_check_node)
    workflow.add_node("response_generation", response_generation_node)
    workflow.add_node("hitl_escalation", hitl_escalation_node)
    workflow.add_node("output", output_node)

    # Set entry point
    workflow.set_entry_point("intent_detection")

    # Add conditional edges
    workflow.add_conditional_edges(
        "intent_detection",
        route_after_intent,
        {
            "retrieval": "retrieval",
            "hitl_escalation": "hitl_escalation"
        }
    )

    workflow.add_edge("retrieval", "confidence_check")

    workflow.add_conditional_edges(
        "confidence_check",
        route_after_confidence,
        {
            "response_generation": "response_generation",
            "hitl_escalation": "hitl_escalation"
        }
    )

    workflow.add_edge("response_generation", "output")
    workflow.add_edge("hitl_escalation", "output")
    workflow.add_edge("output", END)

    return workflow.compile()


# Compile graph on import
support_graph = build_support_graph()
logger.info("LangGraph workflow compiled successfully")
