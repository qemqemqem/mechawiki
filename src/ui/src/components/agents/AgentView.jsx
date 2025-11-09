import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './AgentView.css'

function AgentView({ agent, onBack, onPause, onResume, onArchive, onSendMessage, onOpenFile }) {
  const [logs, setLogs] = useState([])
  const [message, setMessage] = useState('')
  const [showTimestamps, setShowTimestamps] = useState(false)
  const [expandedTools, setExpandedTools] = useState({}) // Track which tools are expanded
  const [hasScrolledInitially, setHasScrolledInitially] = useState(false)
  const logsEndRef = useRef(null)
  const logsContainerRef = useRef(null)

  useEffect(() => {
    let eventSource = null
    let reconnectTimeout = null
    let isMounted = true
    
    const connectToLogs = () => {
      if (!isMounted) return
      
      // Connect to agent logs SSE
      eventSource = new EventSource(`http://localhost:5000/api/agents/${agent.id}/logs`)
      
      eventSource.onmessage = (event) => {
        try {
          const logEntry = JSON.parse(event.data)
          
          // Handle message accumulation - if the last log is also a message, append to it
          setLogs(prev => {
            if (prev.length === 0) {
              return [logEntry]
            }
            
            const lastLog = prev[prev.length - 1]
            
            // Accumulate consecutive messages into one bubble
            if (logEntry.type === 'message' && lastLog.type === 'message') {
              return [
                ...prev.slice(0, -1),
                {
                  ...lastLog,
                  content: lastLog.content + logEntry.content
                }
              ]
            }
            
            // Accumulate consecutive thinking entries
            if (logEntry.type === 'thinking' && lastLog.type === 'thinking') {
              return [
                ...prev.slice(0, -1),
                {
                  ...lastLog,
                  content: lastLog.content + logEntry.content
                }
              ]
            }
            
            // Otherwise, append as new entry
            return [...prev, logEntry]
          })
        } catch (error) {
          // Ignore parse errors (keepalive messages, etc.)
        }
      }
      
      eventSource.onerror = () => {
        console.error('❌ SSE connection error, reconnecting in 3 seconds...')
        eventSource.close()
        
        // Reconnect after 3 seconds if still mounted
        if (isMounted) {
          reconnectTimeout = setTimeout(connectToLogs, 3000)
        }
      }
    }
    
    connectToLogs()
    
    return () => {
      isMounted = false
      if (eventSource) eventSource.close()
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
    }
  }, [agent.id])

  // Initial scroll to bottom when logs first load
  useEffect(() => {
    if (logs.length > 0 && !hasScrolledInitially) {
      logsEndRef.current?.scrollIntoView({ behavior: 'auto' })
      setHasScrolledInitially(true)
    }
  }, [logs, hasScrolledInitially])

  useEffect(() => {
    // Auto-scroll to bottom only if user is already at or near the bottom
    const container = logsContainerRef.current
    if (!container) return
    
    const threshold = 100 // pixels from bottom to consider "at bottom"
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < threshold
    
    if (isNearBottom) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  const handleSendMessage = (e) => {
    e.preventDefault()
    if (message.trim()) {
      onSendMessage(message)
      setMessage('')
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false 
    })
  }

  const formatToolName = (toolName, toolArgs) => {
    // Convert snake_case to Title Case
    const displayName = toolName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
    
    // Add inline details for common tools
    if (!toolArgs) return displayName
    
    // read_article uses "article_name" field
    if (toolName === 'read_article' && toolArgs.article_name) {
      return `${displayName}: ${toolArgs.article_name}`
    }
    if (toolName === 'search_articles' && toolArgs.query) {
      return `${displayName}: "${toolArgs.query}"`
    }
    // edit_article might use article_name or title
    if (toolName === 'edit_article' && (toolArgs.article_name || toolArgs.title)) {
      return `${displayName}: ${toolArgs.article_name || toolArgs.title}`
    }
    if (toolName === 'list_articles_in_directory') {
      return `${displayName}: ${toolArgs.directory || 'articles'}`
    }
    if ((toolName === 'read_file' || toolName === 'edit_file') && toolArgs.filepath) {
      return `${displayName}: ${toolArgs.filepath}`
    }
    if (toolName === 'add_to_story' && toolArgs.filepath) {
      return `${displayName}: ${toolArgs.filepath}`
    }
    // add_to_my_story doesn't need filepath since it's bound to the agent
    if (toolName === 'add_to_my_story') {
      return displayName
    }
    
    // General rule: if there's exactly one argument and it fits in 100 chars, show it inline
    const argKeys = Object.keys(toolArgs)
    if (argKeys.length === 1) {
      const argKey = argKeys[0]
      const argValue = toolArgs[argKey]
      const argString = String(argValue)
      
      if (argString.length <= 100) {
        return `${displayName}: ${argString}`
      }
    }
    
    return displayName
  }

  const renderLogEntry = (log, index) => {
    const { type } = log
    const timestamp = showTimestamps && log.timestamp ? (
      <span className="log-timestamp">{formatTimestamp(log.timestamp)}</span>
    ) : null
    
    const isToolExpanded = expandedTools[index] || false
    
    // Thinking - italics, grey, no bubble
    if (type === 'thinking') {
      return (
        <div key={index} className="log-thinking">
          🤔 {log.content}
          {timestamp}
        </div>
      )
    }
    
    // Tool call - collapsed by default
    if (type === 'tool_call') {
      // Special handling for story writing tools - render as prominent story bubble
      if ((log.tool === 'add_to_story' || log.tool === 'add_to_my_story') && log.args && log.args.content) {
        return (
          <div key={index} className="log-story-bubble">
            <div className="story-label">📖 Story</div>
            <div className="story-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {log.args.content}
              </ReactMarkdown>
            </div>
            {timestamp}
          </div>
        )
      }
      
      // Find the matching tool_result in the next few log entries
      let toolResult = null
      for (let i = index + 1; i < Math.min(index + 5, logs.length); i++) {
        if (logs[i].type === 'tool_result' && logs[i].tool === log.tool) {
          toolResult = logs[i].result
          break
        }
      }
      
      return (
        <div key={index} className="log-tool">
          <div 
            className="tool-call-header"
            onClick={() => setExpandedTools(prev => ({ ...prev, [index]: !prev[index] }))}
          >
            <span className="tool-name">Tool: {formatToolName(log.tool, log.args)}</span>
            <span className="tool-expand">{isToolExpanded ? '▼' : '▶'}</span>
          </div>
          {isToolExpanded && (
            <div className="tool-details">
              {log.args && Object.keys(log.args).length > 0 && (
                <div className="tool-section">
                  <div className="tool-section-label">Arguments:</div>
                  <pre className="tool-args">{JSON.stringify(log.args, null, 2)}</pre>
                </div>
              )}
              {toolResult && (
                <div className="tool-section">
                  <div className="tool-section-label">Response:</div>
                  <pre className="tool-result">{typeof toolResult === 'string' ? toolResult : JSON.stringify(toolResult, null, 2)}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      )
    }
    
    // Tool result - hide since we show it inline with tool_call
    if (type === 'tool_result') {
      return null
    }
    
    // Status messages - small and subtle
    if (type === 'status') {
      return (
        <div key={index} className="log-status">
          Status: <strong>{log.status}</strong> - {log.message}
          {timestamp}
        </div>
      )
    }
    
    // Agent messages - chat bubble style (no robot emoji)
    if (type === 'message') {
      return (
        <div key={index} className="log-message-bubble">
          <div className="log-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {log.content}
            </ReactMarkdown>
          </div>
          {timestamp}
        </div>
      )
    }
    
    // User messages - chat bubble style (right aligned)
    if (type === 'user_message') {
      return (
        <div key={index} className="log-user-bubble">
          <div className="log-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {log.content}
            </ReactMarkdown>
          </div>
          {timestamp}
        </div>
      )
    }
    
    // Error messages - prominent red display
    if (type === 'error') {
      return (
        <div key={index} className="log-error">
          <div className="error-header">
            <span className="error-icon">⚠️</span>
            <span className="error-title">Error</span>
          </div>
          <div className="error-message">{log.error}</div>
          {log.traceback && (
            <details className="error-traceback">
              <summary>Traceback</summary>
              <pre>{log.traceback}</pre>
            </details>
          )}
          {timestamp}
        </div>
      )
    }
    
    return null
  }

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
          {(agent.status === 'paused' || agent.status === 'waiting_for_input' || agent.status === 'finished' || agent.status === 'error_waiting') && (
            <button onClick={onResume}>▶ Resume</button>
          )}
          <button onClick={onArchive} className="danger">📦 Archive</button>
        </div>
      </div>

      <div className="agent-view-options">
        <div className="agent-info-compact">
          {agent.type} • {agent.status}
          {agent.story_file && (
            <>
              {' • '}
              <button 
                className="story-link" 
                onClick={() => onOpenFile(agent.story_file)}
                title={`Open ${agent.story_file}`}
              >
                📖 Story
              </button>
            </>
          )}
        </div>
        <label className="timestamp-checkbox">
          <input
            type="checkbox"
            checked={showTimestamps}
            onChange={(e) => setShowTimestamps(e.target.checked)}
          />
          Show Timestamps
        </label>
      </div>

      <div className="agent-logs" ref={logsContainerRef}>
        {logs.length === 0 ? (
          <div className="empty-state">
            <p>No activity yet...</p>
          </div>
        ) : (
          logs.map((log, index) => renderLogEntry(log, index))
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

