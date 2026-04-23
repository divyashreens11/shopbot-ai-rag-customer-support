import React, { useState, useEffect } from 'react';
import './AgentDashboard.css';

const API_BASE = '/api/v1';

export default function AgentDashboard() {
  const [escalations, setEscalations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [responding, setResponding] = useState({});
  const [responses, setResponses] = useState({});
  const [resolved, setResolved] = useState([]);

  const fetchEscalations = async () => {
    try {
      const res = await fetch(`${API_BASE}/escalations`);
      const data = await res.json();
      setEscalations(data.escalations || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchEscalations();
    const interval = setInterval(fetchEscalations, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRespond = async (sessionId) => {
    const resp = responses[sessionId];
    if (!resp?.trim()) return;

    setResponding(prev => ({ ...prev, [sessionId]: true }));

    try {
      const res = await fetch(`${API_BASE}/escalations/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          human_agent_response: resp,
          agent_name: 'Support Agent'
        })
      });

      if (res.ok) {
        const data = await res.json();
        setResolved(prev => [...prev, { ...data, session_id: sessionId }]);
        setEscalations(prev => prev.filter(e => e.session_id !== sessionId));
      }
    } catch (e) { console.error(e); }
    finally { setResponding(prev => ({ ...prev, [sessionId]: false })); }
  };

  const hitlSteps = [
    { icon: '🔍', label: 'Detection', desc: 'Keywords or low confidence triggers escalation' },
    { icon: '📋', label: 'Ticket Created', desc: 'Session logged with query and reason' },
    { icon: '👤', label: 'Agent Assigned', desc: 'Human agent reviews in this dashboard' },
    { icon: '✅', label: 'Resolution', desc: 'Response sent back to customer' },
  ];

  return (
    <div className="agent-page">
      <div className="agent-header">
        <div>
          <h2>Human Agent Dashboard</h2>
          <p>Review and respond to escalated customer queries</p>
        </div>
        <div className="agent-stats">
          <div className="astat"><span>{escalations.length}</span>Pending</div>
          <div className="astat"><span>{resolved.length}</span>Resolved</div>
        </div>
      </div>

      <div className="agent-layout">
        <div className="agent-main">
          {loading && <div className="loading-state">Loading escalations...</div>}

          {!loading && escalations.length === 0 && resolved.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">✅</div>
              <h3>No Pending Escalations</h3>
              <p>All queries are being handled by the AI. Escalations will appear here when triggered.</p>
              <p className="empty-hint">Trigger conditions: sensitive keywords (fraud, refund, legal), low confidence, or no knowledge base match.</p>
            </div>
          )}

          {escalations.map(esc => (
            <div key={esc.session_id} className="escalation-card">
              <div className="esc-header">
                <div className="esc-id">
                  <span className="badge badge-danger">🔴 PENDING</span>
                  <span className="esc-session">Session: {esc.session_id?.slice(-8)}</span>
                </div>
                <div className="esc-time">
                  {new Date(esc.timestamp).toLocaleTimeString()}
                </div>
              </div>

              <div className="esc-query">
                <label>Customer Query</label>
                <p>"{esc.query}"</p>
              </div>

              <div className="esc-reason">
                <label>Escalation Reason</label>
                <p>{esc.reason}</p>
              </div>

              <div className="esc-response-area">
                <label>Your Response</label>
                <textarea
                  placeholder="Type your response to the customer..."
                  value={responses[esc.session_id] || ''}
                  onChange={e => setResponses(prev => ({ ...prev, [esc.session_id]: e.target.value }))}
                  rows={3}
                  className="agent-textarea"
                />
                <button
                  className="btn btn-primary"
                  onClick={() => handleRespond(esc.session_id)}
                  disabled={responding[esc.session_id] || !responses[esc.session_id]?.trim()}
                >
                  {responding[esc.session_id] ? <><div className="spinner" /> Sending...</> : '📤 Send Response'}
                </button>
              </div>
            </div>
          ))}

          {resolved.map((r, i) => (
            <div key={i} className="escalation-card resolved">
              <div className="esc-header">
                <span className="badge badge-success">✅ RESOLVED</span>
                <span className="esc-session">Session: {r.session_id?.slice(-8)}</span>
              </div>
              <div className="esc-query">
                <label>Original Query</label>
                <p>"{r.original_query}"</p>
              </div>
              <div className="esc-query">
                <label>Your Response</label>
                <p>{r.response}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="agent-sidebar">
          <div className="card">
            <h4>🔄 HITL Workflow</h4>
            <div className="hitl-steps">
              {hitlSteps.map((s, i) => (
                <div key={i} className="hitl-step">
                  <div className="hitl-step-icon">{s.icon}</div>
                  <div>
                    <div className="hitl-step-label">{s.label}</div>
                    <div className="hitl-step-desc">{s.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h4>⚡ HITL Triggers</h4>
            <div className="trigger-list">
              {[
                ['Sensitive Keywords', 'fraud, legal, lawsuit, refund, urgent...'],
                ['Low Confidence', 'Similarity score < 35%'],
                ['No Context Found', 'Zero relevant chunks retrieved'],
                ['Complex Queries', 'Multi-step or ambiguous intent'],
              ].map(([k, v]) => (
                <div key={k} className="trigger-item">
                  <div className="trigger-key">{k}</div>
                  <div className="trigger-val">{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
