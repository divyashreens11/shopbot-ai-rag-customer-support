# 🤖 ShopBot AI — RAG Customer Support Assistant
 
> **Stack:** FastAPI · React · OpenAI GPT-3.5 · ChromaDB · LangGraph · HITL

---

## 📌 Project Overview

ShopBot AI is a **production-grade RAG (Retrieval-Augmented Generation)** customer support assistant for e-commerce. It ingests a PDF knowledge base, retrieves relevant context using semantic search, and generates accurate, grounded responses using OpenAI GPT-3.5. A LangGraph workflow orchestrates the multi-step decision pipeline with intelligent Human-in-the-Loop (HITL) escalation.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     REACT FRONTEND (Port 3000)                  │
│   Chat Interface  │  Document Upload  │  Agent Dashboard        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST
┌───────────────────────────▼─────────────────────────────────────┐
│                    FASTAPI BACKEND (Port 8000)                   │
│     /ingest    │    /query    │    /escalations   │   /stats     │
└───────┬────────────────┬────────────────────────────────────────┘
        │                │
┌───────▼──────┐  ┌──────▼───────────────────────────────────────┐
│  Document    │  │           LANGGRAPH WORKFLOW                  │
│  Processor   │  │                                               │
│  + Chunker   │  │  1. IntentDetection                           │
└───────┬──────┘  │  2. Retrieval                                 │
        │         │  3. ConfidenceCheck                           │
        │         │  4. ResponseGeneration  OR  HITLEscalation    │
        │         │  5. Output                                    │
        │         └──────┬──────────────────┬────────────────────┘
        │                │                  │
┌───────▼──────┐  ┌──────▼───────┐  ┌──────▼────────────────────┐
│  ChromaDB    │  │  OpenAI LLM  │  │  HITL Escalation Engine   │
│  Vector Store│  │  GPT-3.5     │  │  Session Store + Agents   │
└──────────────┘  └──────────────┘  └───────────────────────────┘
```

---

## 🔄 LangGraph Workflow

```
START
  │
  ▼
[Intent Detection] ──── HITL keyword? ──YES──▶ [HITL Escalation]
  │                                                    │
  NO                                                   │
  ▼                                                    │
[Retrieval] ──▶ [Confidence Check] ─── Low? ──YES──▶──┘
                        │
                        NO
                        ▼
               [Response Generation]
                        │
                        ▼
                    [Output] ──▶ END
```

**HITL Triggers:**
- 🔑 Sensitive keywords: `fraud`, `refund`, `legal`, `lawsuit`, `escalate`, `manager`, `urgent`...
- 📉 Low confidence: mean retrieval score < 0.35
- ❌ No context: zero chunks retrieved from ChromaDB

---

## 📁 Project Structure

```
rag_project/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── api/
│   │   │   └── routes.py            # All REST API endpoints
│   │   ├── core/
│   │   │   ├── config.py            # Settings (OpenAI, ChromaDB, chunking)
│   │   │   ├── document_processor.py # PDF loading + chunking
│   │   │   └── vector_store.py      # ChromaDB manager
│   │   ├── graph/
│   │   │   └── workflow.py          # LangGraph 6-node workflow
│   │   └── models/
│   │       └── schemas.py           # Pydantic request/response models
│   ├── data/
│   │   ├── chromadb/               # Persistent vector store (auto-created)
│   │   └── uploads/                # Uploaded PDFs (auto-created)
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Root component + routing
│   │   ├── App.css                  # Global dark theme styles
│   │   └── components/
│   │       ├── ChatInterface.jsx    # Main chat UI
│   │       ├── ChatInterface.css
│   │       ├── Sidebar.jsx          # Stats + pipeline visualization
│   │       ├── Sidebar.css
│   │       ├── DocumentUpload.jsx   # PDF upload + ingestion UI
│   │       ├── DocumentUpload.css
│   │       ├── AgentDashboard.jsx   # HITL agent panel
│   │       └── AgentDashboard.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API Key

---

### Step 1: Clone / Unzip Project

```bash
cd rag_project
```

---

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 3: Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-actual-key-here
```

---

### Step 4: Start Backend Server

```bash
# From backend/ directory
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Backend will be live at:** `http://localhost:8000`  
**API Docs:** `http://localhost:8000/docs`

---

### Step 5: Frontend Setup

```bash
# Open a new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend will be live at:** `http://localhost:3000`

---

## 🚀 Usage Guide

### 1. Upload Knowledge Base
- Open `http://localhost:3000`
- Click **"📄 Knowledge Base"** tab
- Upload the provided `ecommerce_knowledge_base.pdf` (or your own PDF)
- Wait for ingestion confirmation (shows chunk count)

### 2. Chat with ShopBot
- Click **"💬 Chat"** tab
- Type any customer support question
- View: AI response, intent label, confidence score, retrieved chunks

### 3. Test HITL Escalation
- Type: *"This is fraud! I want to speak to a manager immediately!"*
- System escalates to HITL, shows agent response

### 4. Agent Dashboard
- Click **"👤 Agent Panel"** tab
- View pending escalations
- Submit human responses to tickets

---

## 🔑 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/v1/ingest` | POST | Upload & index PDF |
| `POST /api/v1/query` | POST | Submit support query |
| `GET /api/v1/escalations` | GET | List pending HITL tickets |
| `POST /api/v1/escalations/respond` | POST | Agent responds to ticket |
| `GET /api/v1/stats` | GET | System statistics |
| `GET /health` | GET | Health check |
| `GET /docs` | GET | Interactive API docs |

---

## 🧪 Sample Test Queries

| Query | Expected Behavior |
|-------|-------------------|
| `What is your return policy?` | Returns 30-day policy details |
| `How do I track my order?` | Explains tracking via My Orders |
| `Do you offer free shipping?` | Returns Rs. 499 threshold info |
| `I need a refund, this is fraud!` | **HITL triggered** — escalates to agent |
| `What payment methods are accepted?` | Lists all payment options |
| `How long does delivery take?` | Returns delivery timeline |

---

## 🛠️ Configuration

Edit `backend/.env` to customize:

```env
OPENAI_MODEL=gpt-3.5-turbo        # or gpt-4
CHUNK_SIZE=500                      # Characters per chunk
CHUNK_OVERLAP=50                    # Overlap between chunks
TOP_K_RESULTS=4                     # Chunks retrieved per query
CONFIDENCE_THRESHOLD=0.35           # Min score before HITL
```

---

## 📊 Key Design Choices

| Decision | Choice | Reason |
|----------|--------|--------|
| Chunk size | 500 chars | Balances specificity vs. context |
| Embedding | text-embedding-3-small | Best cost/quality ratio |
| Vector DB | ChromaDB | Zero-config, local, persistent |
| Similarity | Cosine | Length-invariant semantic matching |
| Orchestration | LangGraph | Formal state machine for AI workflows |
| Temperature | 0.3 | Consistent, factual responses |

---

## 🔮 Future Enhancements

- [ ] Redis-backed session persistence
- [ ] Streaming responses (SSE)
- [ ] Multi-document support with namespace isolation
- [ ] Cohere Rerank for improved retrieval precision
- [ ] LangSmith integration for production tracing
- [ ] Docker Compose deployment
- [ ] Feedback loop & continuous improvement

---

