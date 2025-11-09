import { useState } from 'react'
import { formatDistanceToNow } from '../../utils/time'
import './FilesFeed.css'

function FilesFeed({ fileChanges, onSelectFile }) {
  const [filterAgent, setFilterAgent] = useState('all')
  
  // Get unique agents and sort alphabetically
  const agentSet = new Set(fileChanges.map(fc => fc.agent_id || 'unknown'))
  const agents = ['all', ...Array.from(agentSet).sort()]
  
  // Filter file changes
  const filteredChanges = filterAgent === 'all'
    ? fileChanges
    : fileChanges.filter(fc => (fc.agent_id || 'unknown') === filterAgent)
  
  const formatChanges = (changes) => {
    if (!changes) return ''
    const { added = 0, removed = 0 } = changes
    // If both are 0, it's a read operation
    if (added === 0 && removed === 0) return 'read'
    return `+${added} -${removed}`
  }

  if (filteredChanges.length === 0) {
    return (
      <div className="files-feed">
        <div className="feed-filters">
          <label>Filter by Agent:</label>
          <select value={filterAgent} onChange={(e) => setFilterAgent(e.target.value)}>
            {agents.map(agent => (
              <option key={agent} value={agent}>{agent}</option>
            ))}
          </select>
        </div>
        
        <div className="empty-state">
          <div className="empty-state-icon">📚</div>
          <p>No file activity yet</p>
          <p style={{ fontSize: '0.9rem', marginTop: '8px' }}>
            Files modified by agents will appear here
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="files-feed">
      <div className="feed-filters">
        <label>Filter by Agent:</label>
        <select value={filterAgent} onChange={(e) => setFilterAgent(e.target.value)}>
          {agents.map(agent => (
            <option key={agent} value={agent}>{agent}</option>
          ))}
        </select>
      </div>

      <div className="feed-list">
        {filteredChanges.map((change, index) => (
          <div
            key={index}
            className="card feed-item"
            onClick={() => onSelectFile(change.file_path)}
          >
            <div className="feed-item-header">
              <span className="file-icon">📄</span>
              <span className="file-name">{change.file_path}</span>
              <span className="file-changes">{formatChanges(change.changes)}</span>
            </div>
            
            <div className="feed-item-meta">
              <span className="agent-name">{change.agent_id || 'unknown'}</span>
              <span className="separator">•</span>
              <span className="timestamp">{formatDistanceToNow(change.timestamp)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default FilesFeed

