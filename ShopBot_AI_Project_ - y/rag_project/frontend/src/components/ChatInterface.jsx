import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';

const API_BASE = '/api/v1';

const intentColors = {
  product_info: 'info',
  order_status: 'purple',
  return_refund: 'warning',
  shipping: 'info',
  account: 'success',
  complaint: 'danger',
  general: 'info',
  hitl_required: 'danger'
};

const intentLabels = {
  product_info: '📦 Product',
  order_status: '🚚 Order Status',
  return_refund: '↩️ Return/Refund',
  shipping: '📮 Shipping',
  account: '👤 Account',
  complaint: '⚠️ Complaint',
  general: '💬 General',
  hitl_required: '🔴 Escalated'
};

const SAMPLE_QUERIES = [
  "What is your return policy?",
  "How do I track my order?",
  "Do you offer free shipping?",
  "I need a refund immediately - this is fraud!",
  "What payment methods do you accept?",
  "How long does delivery take?"
];

export default function ChatInterface({ sessionId, isIngested, onStatsUpdate }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "👋 Hello! I'm **ShopBot**, your AI-powered customer support assistant. I can help you with orders, shipping, returns, products, and more.\n\nUpload a knowledge base PDF first, then ask me anything!",
      timestamp: new Date(),
      isWelcome: true
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastResponse, setLastResponse] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendQuery = async (query = input) => {
    if (!query.trim() || loading) return;

    const userMsg = { id: Date.now(), role: 'user', content: query, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, session_id: sessionId })
      });

      const data = await res.json();
      setLastResponse(data);

      const botMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        metadata: data
      };

      setMessages(prev => [...prev, botMsg]);
      onStatsUpdate?.();
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: '❌ Connection error. Make sure the backend server is running on port 8000.',
        timestamp: new Date(),
        isError: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuery(); }
  };

  const formatContent = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>');
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.role} ${msg.isError ? 'error' : ''}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-body">
              <div
                className="message-content"
                dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }}
              />
              {msg.metadata && (
                <div className="message-meta">
                  <span className={`badge badge-${intentColors[msg.metadata.intent] || 'info'}`}>
                    {intentLabels[msg.metadata.intent] || msg.metadata.intent}
                  </span>
                  <span className="meta-item">
                    🎯 {(msg.metadata.confidence * 100).toFixed(0)}% confidence
                  </span>
                  <span className="meta-item">
                    ⚡ {msg.metadata.processing_time_ms?.toFixed(0)}ms
                  </span>
                  {msg.metadata.is_escalated && (
                    <span className="badge badge-danger">🔴 HITL Escalated</span>
                  )}
                </div>
              )}
              {msg.metadata?.human_response && (
                <div className="human-response-box">
                  <div className="hr-header">👤 Human Agent Response</div>
                  <p>{msg.metadata.human_response}</p>
                </div>
              )}
              {msg.metadata?.retrieved_chunks?.length > 0 && (
                <details className="chunks-details">
                  <summary>📚 {msg.metadata.retrieved_chunks.length} source chunks retrieved</summary>
                  <div className="chunks-list">
                    {msg.metadata.retrieved_chunks.map((c, i) => (
                      <div key={i} className="chunk-item">
                        <div className="chunk-header">
                          <span>Chunk #{i + 1}</span>
                          <span className="chunk-score">{(c.relevance_score * 100).toFixed(0)}% match</span>
                        </div>
                        <p className="chunk-text">{c.content.slice(0, 200)}...</p>
                      </div>
                    ))}
                  </div>
                </details>
              )}
              <span className="message-time">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-body">
              <div className="typing-indicator">
                <span/><span/><span/>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {!isIngested && (
        <div className="sample-queries">
          <p className="sq-label">Try these sample queries (after uploading PDF):</p>
          <div className="sq-grid">
            {SAMPLE_QUERIES.map((q, i) => (
              <button key={i} className="sq-btn" onClick={() => sendQuery(q)}>
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="chat-input-area">
        <div className="input-wrapper">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about orders, shipping, returns, products..."
            rows={1}
            className="chat-input"
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={() => sendQuery()}
            disabled={loading || !input.trim()}
          >
            {loading ? <div className="spinner" /> : '→'}
          </button>
        </div>
        <p className="input-hint">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}
