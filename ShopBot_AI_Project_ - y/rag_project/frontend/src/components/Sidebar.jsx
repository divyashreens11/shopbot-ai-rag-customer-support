import React from 'react';
import './Sidebar.css';

export default function Sidebar({ stats }) {
  const items = [
    { label: 'Chunks Indexed', value: stats?.vector_store?.count ?? '—', icon: '📚', color: 'green' },
    { label: 'Active Sessions', value: stats?.active_sessions ?? '—', icon: '💬', color: 'blue' },
    { label: 'Pending HITL', value: stats?.pending_escalations ?? '—', icon: '🔴', color: 'red' },
    { label: 'LLM Model', value: stats?.model?.replace('gpt-', 'GPT-') ?? '—', icon: '🧠', color: 'purple' },
    { label: 'Embedding', value: stats?.embedding_model?.split('-').slice(-2).join('-') ?? '—', icon: '🔢', color: 'teal' },
    { label: 'Chunk Size', value: stats?.chunk_size ? `${stats.chunk_size} tokens` : '—', icon: '✂️', color: 'orange' },
    { label: 'Top-K Retrieval', value: stats?.top_k ? `${stats.top_k} chunks` : '—', icon: '🎯', color: 'blue' },
    { label: 'Confidence Thr.', value: stats?.confidence_threshold ? `${(stats.confidence_threshold * 100).toFixed(0)}%` : '—', icon: '📊', color: 'green' },
  ];

  const pipeline = [
    { step: '01', label: 'PDF Ingestion', desc: 'Upload & extract text' },
    { step: '02', label: 'Chunking', desc: 'Split into 500-token chunks' },
    { step: '03', label: 'Embedding', desc: 'OpenAI text-embedding-3-small' },
    { step: '04', label: 'ChromaDB', desc: 'Cosine similarity storage' },
    { step: '05', label: 'LangGraph', desc: '6-node workflow execution' },
    { step: '06', label: 'Response / HITL', desc: 'GPT or human escalation' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <h3 className="sidebar-title">System Stats</h3>
        <div className="stats-grid">
          {items.map((item, i) => (
            <div key={i} className={`stat-card stat-${item.color}`}>
              <span className="stat-icon">{item.icon}</span>
              <div>
                <div className="stat-value">{item.value}</div>
                <div className="stat-label">{item.label}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="sidebar-section">
        <h3 className="sidebar-title">RAG Pipeline</h3>
        <div className="pipeline">
          {pipeline.map((p, i) => (
            <div key={i} className="pipeline-step">
              <div className="step-number">{p.step}</div>
              <div className="step-content">
                <div className="step-label">{p.label}</div>
                <div className="step-desc">{p.desc}</div>
              </div>
              {i < pipeline.length - 1 && <div className="step-connector" />}
            </div>
          ))}
        </div>
      </div>

      <div className="sidebar-section">
        <h3 className="sidebar-title">Workflow</h3>
        <div className="workflow-info">
          <div className="wf-node green">Intent Detection</div>
          <div className="wf-arrow">↓</div>
          <div className="wf-node blue">Semantic Retrieval</div>
          <div className="wf-arrow">↓</div>
          <div className="wf-node orange">Confidence Check</div>
          <div className="wf-branch">
            <div className="wf-branch-item">
              <div className="wf-node green">GPT Response</div>
            </div>
            <div className="wf-branch-item">
              <div className="wf-node red">HITL Escalation</div>
            </div>
          </div>
          <div className="wf-arrow">↓</div>
          <div className="wf-node purple">Final Output</div>
        </div>
      </div>
    </aside>
  );
}
