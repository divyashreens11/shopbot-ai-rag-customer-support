import React, { useState, useRef, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import DocumentUpload from './components/DocumentUpload';
import AgentDashboard from './components/AgentDashboard';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [sessionId] = useState(`session_${Date.now()}`);
  const [stats, setStats] = useState(null);
  const [isIngested, setIsIngested] = useState(false);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/v1/stats');
      const data = await res.json();
      setStats(data);
      if (data.vector_store?.count > 0) setIsIngested(true);
    } catch (e) {
      console.error('Stats fetch error:', e);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-icon">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <circle cx="14" cy="14" r="13" stroke="#00D4AA" strokeWidth="2"/>
              <path d="M8 14h12M14 8v12" stroke="#00D4AA" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="14" cy="14" r="3" fill="#00D4AA"/>
            </svg>
          </div>
          <div>
            <h1 className="brand-name">ShopBot AI</h1>
            <span className="brand-sub">RAG Customer Support Assistant</span>
          </div>
        </div>
        <div className="header-nav">
          {['chat', 'upload', 'agents'].map(tab => (
            <button
              key={tab}
              className={`nav-btn ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'chat' ? '💬 Chat' : tab === 'upload' ? '📄 Knowledge Base' : '👤 Agent Panel'}
            </button>
          ))}
        </div>
        <div className="header-status">
          <div className={`status-dot ${isIngested ? 'online' : 'offline'}`} />
          <span>{isIngested ? `${stats?.vector_store?.count || 0} chunks indexed` : 'No knowledge base'}</span>
        </div>
      </header>

      <main className="app-main">
        {activeTab === 'chat' && (
          <div className="chat-layout">
            <Sidebar stats={stats} />
            <ChatInterface sessionId={sessionId} isIngested={isIngested} onStatsUpdate={fetchStats} />
          </div>
        )}
        {activeTab === 'upload' && (
          <DocumentUpload onIngested={() => { setIsIngested(true); fetchStats(); }} />
        )}
        {activeTab === 'agents' && (
          <AgentDashboard />
        )}
      </main>
    </div>
  );
}

export default App;
