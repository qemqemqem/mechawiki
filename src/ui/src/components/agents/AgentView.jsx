import { useState, useEffect, useRef } from 'react'
import './AgentView.css'

function AgentView({ agent, onBack, onPause, onResume, onArchive, onSendMessage }) {
  const [logs, setLogs] = useState([])
  const [message, setMessage] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const logsEndRef = useRef(null)

  useEffect(() => {
    // Connect to agent logs SSE
    const eventSource = new EventSource(`http://localhost:5000/api/agents/${agent.id}/logs`)
    
    eventSource.onmessage = (event) => {
      try {
        const logEntry = JSON.parse(event.data)
        setLogs(prev => [...prev, logEntry])
      } catch (error) {
        // Ignore parse errors
      }
    }
    
    eventSource.onerror = () => {
      console.error('Error connecting to agent logs')
      eventSource.close()
    }
    
    return () => eventSource.close()
  }, [agent.id])

  useEffect(() => {
    // Auto-scroll to bottom
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const handleSendMessage = (e) => {
    e.preventDefault()
    if (message.trim()) {
      onSendMessage(message)
      setMessage('')
    }
  }

  const filterLogs = () => {
    if (activeTab === 'all') return logs
    if (activeTab === 'messages') return logs.filter(l => l.type === 'message' || l.type === 'user_message')
    if (activeTab === 'tools') return logs.filter(l => l.type === 'tool_call' || l.type === 'tool_result')
    if (activeTab === 'thinking') return logs.filter(l => l.type === 'thinking')
    return logs
  }

  const renderLogEntry = (log, index) => {
    const { type } = log
    
    if (type === 'status') {
      return (
        <div key={index} className="log-entry log-status">
          <span className="log-icon">ℹ️</span>
          <span className="log-content">
            Status: <strong>{log.status}</strong> - {log.message}
          </span>
        </div>
      )
    }
    
    if (type === 'tool_call') {
      return (
        <div key={index} className="log-entry log-tool-call">
          <span className="log-icon">🔧</span>
          <span className="log-content">
            <strong>{log.tool}()</strong>
            {log.args && <div className="log-args">{JSON.stringify(log.args, null, 2)}</div>}
          </span>
        </div>
      )
    }
    
    if (type === 'tool_result') {
      return (
        <div key={index} className="log-entry log-tool-result">
          <span className="log-icon">✓</span>
          <span className="log-content">
            Result: {JSON.stringify(log.result)}
          </span>
        </div>
      )
    }
    
    if (type === 'message') {
      return (
        <div key={index} className="log-entry log-message">
          <span className="log-icon">🤖</span>
          <span className="log-content">{log.content}</span>
        </div>
      )
    }
    
    if (type === 'user_message') {
      return (
        <div key={index} className="log-entry log-user-message">
          <span className="log-icon">👤</span>
          <span className="log-content">{log.content}</span>
        </div>
      )
    }
    
    if (type === 'thinking') {
      return (
        <div key={index} className="log-entry log-thinking">
          <span className="log-icon">🧠</span>
          <span className="log-content">{log.content}</span>
        </div>
      )
    }
    
    return null
  }

  const filteredLogs = filterLogs()

  return (
    <div className="agent-view">
      <div className="agent-view-header">
        <button onClick={onBack} className="back-button">
          ← Back to Command Center
        </button>
        
        <div className="agent-controls">
          {agent.status === 'running' && (
            <button onClick={onPause}>⏸ Pause</button>
          )}
          {(agent.status === 'paused' || agent.status === 'waiting_for_input') && (
            <button onClick={onResume}>▶ Resume</button>
          )}
          <button onClick={onArchive} className="danger">📦 Archive</button>
        </div>
      </div>

      <div className="agent-info">
        <h3>{agent.name}</h3>
        <p>{agent.type} • {agent.status}</p>
      </div>

      <div className="agent-tabs">
        <button
          className={activeTab === 'all' ? 'active' : ''}
          onClick={() => setActiveTab('all')}
        >
          All
        </button>
        <button
          className={activeTab === 'messages' ? 'active' : ''}
          onClick={() => setActiveTab('messages')}
        >
          Messages
        </button>
        <button
          className={activeTab === 'tools' ? 'active' : ''}
          onClick={() => setActiveTab('tools')}
        >
          Tools
        </button>
        <button
          className={activeTab === 'thinking' ? 'active' : ''}
          onClick={() => setActiveTab('thinking')}
        >
          Thinking
        </button>
      </div>

      <div className="agent-logs">
        {filteredLogs.length === 0 ? (
          <div className="empty-state">
            <p>No activity yet...</p>
          </div>
        ) : (
          filteredLogs.map((log, index) => renderLogEntry(log, index))
        )}
        <div ref={logsEndRef} />
      </div>

      <form className="agent-chat-input" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message..."
          autoFocus
        />
        <button type="submit" disabled={!message.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}

export default AgentView

