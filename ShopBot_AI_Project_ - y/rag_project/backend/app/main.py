"""
RAG-Based Customer Support Assistant
Backend: FastAPI + LangGraph + ChromaDB + OpenAI
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from app.api.routes import router
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Customer Support Assistant",
    description="AI-powered customer support using RAG, LangGraph, and HITL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "RAG Customer Support Assistant API",
        "version": "1.0.0",
        "author": "Divyashree N S",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "RAG-Support-API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
