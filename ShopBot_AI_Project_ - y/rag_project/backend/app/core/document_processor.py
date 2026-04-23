"""
Document Processing Module
Handles PDF ingestion, chunking, and embedding storage
"""
import os
import logging
import hashlib
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentChunk:
    def __init__(self, content: str, metadata: dict, chunk_id: str):
        self.content = content
        self.metadata = metadata
        self.chunk_id = chunk_id


class DocumentProcessor:
    """
    Handles PDF loading, text extraction, and intelligent chunking.
    Strategy: Recursive character text splitting with overlap for context preservation.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_pdf(self, pdf_path: str) -> str:
        """Extract raw text from PDF using pypdf"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            full_text = ""
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text += f"\n[Page {page_num + 1}]\n{text}\n"
            logger.info(f"Extracted {len(full_text)} characters from {pdf_path}")
            return full_text
        except Exception as e:
            logger.error(f"PDF loading error: {e}")
            raise

    def chunk_text(self, text: str, source: str = "document") -> List[DocumentChunk]:
        """
        Recursive character-based chunking with overlap.
        Splits on paragraphs → sentences → words to preserve semantic coherence.
        """
        separators = ["\n\n", "\n", ". ", " ", ""]
        chunks = self._recursive_split(text, separators, self.chunk_size)

        document_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_text = chunk_text.strip()
            if len(chunk_text) < 30:  # Skip very small chunks
                continue

            chunk_id = hashlib.md5(f"{source}_{i}_{chunk_text[:50]}".encode()).hexdigest()[:12]
            metadata = {
                "source": source,
                "chunk_index": i,
                "chunk_size": len(chunk_text),
                "chunk_id": chunk_id
            }
            document_chunks.append(DocumentChunk(chunk_text, metadata, chunk_id))

        logger.info(f"Created {len(document_chunks)} chunks from document")
        return document_chunks

    def _recursive_split(self, text: str, separators: List[str], chunk_size: int) -> List[str]:
        """Recursively split text by separators"""
        chunks = []
        separator = separators[0] if separators else ""

        if separator:
            parts = text.split(separator)
        else:
            parts = list(text)

        current_chunk = ""
        for part in parts:
            test = (current_chunk + separator + part).strip() if current_chunk else part.strip()
            if len(test) <= chunk_size:
                current_chunk = test
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Add overlap
                    overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap else ""
                    current_chunk = (overlap_text + " " + part).strip() if overlap_text else part.strip()
                else:
                    if len(part) <= chunk_size:
                        current_chunk = part
                    else:
                        if len(separators) > 1:
                            sub_chunks = self._recursive_split(part, separators[1:], chunk_size)
                            chunks.extend(sub_chunks)
                        else:
                            chunks.append(part)
                        current_chunk = ""

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def process_pdf(self, pdf_path: str) -> List[DocumentChunk]:
        """Full pipeline: load → extract → chunk"""
        source_name = Path(pdf_path).stem
        raw_text = self.load_pdf(pdf_path)
        chunks = self.chunk_text(raw_text, source=source_name)
        return chunks
