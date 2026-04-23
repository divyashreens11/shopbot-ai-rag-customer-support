"""
Vector Store Module - Google Gemini embeddings
Uses Google Gemini API for embeddings (free tier available).
"""
import os
import json
import logging
import numpy as np
from typing import List, Dict
import google.genai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        self.documents = []
        self.metadatas = []
        self.ids = []
        self.embeddings = []
        self._initialized = False
        self._persist_path = os.path.join(settings.CHROMA_PERSIST_DIR, "vectorstore.json")
        self._client = None

    def initialize(self):
        # Check if Gemini API key is configured
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != 'your-gemini-api-key-here':
            self._use_gemini = True
            logger.info("Using Google Gemini for embeddings")
        else:
            self._use_gemini = False
            logger.warning("No Gemini API key found, embeddings will fail")

        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        if os.path.exists(self._persist_path):
            try:
                with open(self._persist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.documents  = data.get("documents", [])
                self.metadatas  = data.get("metadatas", [])
                self.ids        = data.get("ids", [])
                self.embeddings = data.get("embeddings", [])
                logger.info(f"Loaded {len(self.documents)} chunks from disk")
            except Exception as e:
                logger.warning(f"Could not load persisted store: {e}")
        self._initialized = True
        return True

    def _embed(self, texts):
        if not self._use_gemini:
            raise Exception("Gemini API key not configured")

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            # Handle batch embedding using working model
            embeddings = []
            for text in texts:
                result = client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=text
                )
                embeddings.append(result.embeddings[0].values)

            return embeddings
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise

    def _cosine_similarity(self, query_vec, matrix):
        q = np.array(query_vec)
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        m_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
        return m_norm @ q_norm

    def _persist(self):
        with open(self._persist_path, "w", encoding="utf-8") as f:
            json.dump({"documents": self.documents, "metadatas": self.metadatas,
                       "ids": self.ids, "embeddings": self.embeddings}, f)

    def add_documents(self, chunks):
        if not self._initialized:
            self.initialize()
        batch_size = 50
        total_added = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [c.content for c in batch]
            vecs  = self._embed(texts)
            for chunk, vec in zip(batch, vecs):
                if chunk.chunk_id not in self.ids:
                    self.documents.append(chunk.content)
                    self.metadatas.append(chunk.metadata)
                    self.ids.append(chunk.chunk_id)
                    self.embeddings.append(vec)
            total_added += len(batch)
            logger.info(f"Embedded batch {i//batch_size+1}: {len(batch)} chunks")
        self._persist()
        return total_added

    def retrieve(self, query, top_k=None):
        if not self._initialized:
            self.initialize()
        top_k = top_k or settings.TOP_K_RESULTS
        if not self.embeddings:
            return []
        query_vec = self._embed([query])[0]
        matrix    = np.array(self.embeddings)
        scores    = self._cosine_similarity(query_vec, matrix)
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append({
                "content":         self.documents[idx],
                "source":          self.metadatas[idx].get("source", "unknown"),
                "relevance_score": round(float(scores[idx]), 4),
                "chunk_id":        self.ids[idx],
                "chunk_index":     self.metadatas[idx].get("chunk_index", int(idx))
            })
        return results

    def get_collection_stats(self):
        if not self._initialized:
            try:
                self.initialize()
            except:
                return {"count": 0, "initialized": False}
        return {"count": len(self.documents),
                "collection_name": settings.CHROMA_COLLECTION_NAME,
                "initialized": True}

    def clear_collection(self):
        self.documents = []
        self.metadatas = []
        self.ids = []
        self.embeddings = []
        self._persist()
        logger.info("Collection cleared")

vector_store = VectorStoreManager()
