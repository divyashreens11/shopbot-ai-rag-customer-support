import React, { useState, useRef } from 'react';
import './DocumentUpload.css';

const API_BASE = '/api/v1';

export default function DocumentUpload({ onIngested }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | uploading | success | error
  const [result, setResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef();

  const handleFile = (f) => {
    if (f && f.type === 'application/pdf') setFile(f);
    else alert('Please select a PDF file');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');

    const form = new FormData();
    form.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/ingest`, { method: 'POST', body: form });
      const data = await res.json();
      if (res.ok) {
        setResult(data);
        setStatus('success');
        onIngested?.();
      } else {
        throw new Error(data.detail || 'Upload failed');
      }
    } catch (err) {
      setResult({ error: err.message });
      setStatus('error');
    }
  };

  return (
    <div className="upload-page">
      <div className="upload-header">
        <h2>Knowledge Base Management</h2>
        <p>Upload your e-commerce support PDF to power the RAG system</p>
      </div>

      <div className="upload-layout">
        <div className="upload-main">
          <div
            className={`dropzone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current.click()}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".pdf"
              onChange={(e) => handleFile(e.target.files[0])}
              style={{ display: 'none' }}
            />
            {file ? (
              <div className="file-preview">
                <div className="file-icon">📄</div>
                <div className="file-info">
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{(file.size / 1024).toFixed(1)} KB</div>
                </div>
                <div className="file-ready">✓ Ready to ingest</div>
              </div>
            ) : (
              <div className="drop-prompt">
                <div className="drop-icon">📁</div>
                <div className="drop-text">Drop your PDF here or click to browse</div>
                <div className="drop-hint">Supports: PDF files only</div>
              </div>
            )}
          </div>

          <button
            className="btn btn-primary upload-btn"
            onClick={handleUpload}
            disabled={!file || status === 'uploading'}
          >
            {status === 'uploading' ? (
              <><div className="spinner" /> Processing PDF...</>
            ) : (
              <> ⚡ Ingest into Knowledge Base</>
            )}
          </button>

          {status === 'success' && result && (
            <div className="result-card success">
              <div className="result-icon">✅</div>
              <div>
                <div className="result-title">Ingestion Successful!</div>
                <div className="result-detail">{result.message}</div>
                <div className="result-chips">
                  <span className="badge badge-success">{result.chunks_created} chunks</span>
                  <span className="badge badge-info">{result.collection_name}</span>
                </div>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="result-card error">
              <div className="result-icon">❌</div>
              <div>
                <div className="result-title">Ingestion Failed</div>
                <div className="result-detail">{result?.error}</div>
              </div>
            </div>
          )}
        </div>

        <div className="upload-sidebar">
          <div className="card info-card">
            <h4>📋 Ingestion Pipeline</h4>
            <ol className="pipeline-list">
              <li>PDF uploaded & saved to server</li>
              <li>Text extracted page-by-page</li>
              <li>Split into 500-token chunks with 50-token overlap</li>
              <li>Each chunk embedded via OpenAI <code>text-embedding-3-small</code></li>
              <li>Vectors stored in ChromaDB with cosine similarity index</li>
              <li>Collection ready for semantic queries</li>
            </ol>
          </div>
          <div className="card info-card">
            <h4>⚙️ Configuration</h4>
            <div className="config-list">
              {[
                ['Chunk Size', '500 characters'],
                ['Chunk Overlap', '50 characters'],
                ['Embedding Model', 'text-embedding-3-small'],
                ['Vector DB', 'ChromaDB (cosine)'],
                ['Similarity Metric', 'Cosine distance'],
                ['Top-K Retrieval', '4 chunks'],
              ].map(([k, v]) => (
                <div key={k} className="config-item">
                  <span className="config-key">{k}</span>
                  <span className="config-val">{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
