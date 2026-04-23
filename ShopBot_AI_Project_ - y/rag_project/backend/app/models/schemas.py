"""
Pydantic Models / Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime


class QueryIntent(str, Enum):
    PRODUCT_INFO = "product_info"
    ORDER_STATUS = "order_status"
    RETURN_REFUND = "return_refund"
    SHIPPING = "shipping"
    ACCOUNT = "account"
    COMPLAINT = "complaint"
    GENERAL = "general"
    HITL_REQUIRED = "hitl_required"


class EscalationStatus(str, Enum):
    NONE = "none"
    PENDING = "pending"
    RESOLVED = "resolved"


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    conversation_history: Optional[List[dict]] = []


class RetrievedChunk(BaseModel):
    content: str
    source: str
    relevance_score: float
    chunk_id: str


class QueryResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    intent: QueryIntent
    confidence: float
    retrieved_chunks: List[RetrievedChunk]
    is_escalated: bool
    escalation_status: EscalationStatus
    escalation_reason: Optional[str] = None
    human_response: Optional[str] = None
    timestamp: datetime
    processing_time_ms: float


class HumanResponseRequest(BaseModel):
    session_id: str
    human_agent_response: str
    agent_name: Optional[str] = "Support Agent"


class IngestRequest(BaseModel):
    chunk_size: Optional[int] = 500
    chunk_overlap: Optional[int] = 50


class IngestResponse(BaseModel):
    status: str
    chunks_created: int
    collection_name: str
    message: str


class GraphState(BaseModel):
    """LangGraph State Object"""
    session_id: str
    query: str
    conversation_history: List[dict] = []
    intent: Optional[QueryIntent] = None
    retrieved_chunks: List[dict] = []
    confidence: float = 0.0
    answer: Optional[str] = None
    is_escalated: bool = False
    escalation_reason: Optional[str] = None
    escalation_status: EscalationStatus = EscalationStatus.NONE
    human_response: Optional[str] = None
    error: Optional[str] = None
