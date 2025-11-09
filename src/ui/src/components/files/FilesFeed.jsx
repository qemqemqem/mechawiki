import { useState } from 'react'
import { formatDistanceToNow } from '../../utils/time'
import './FilesFeed.css'

function FilesFeed({ fileChanges, onSelectFile, onSearchModeChange }) {
  const [filterAgent, setFilterAgent] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  
  // Get unique agents and sort alphabetically
  const agentSet = new Set(fileChanges.map(fc => fc.agent_id || 'unknown'))
  const agents = ['all', ...Array.from(agentSet).sort()]
  
  // Determine if we're in search mode
  const isSearchMode = searchQuery.trim().length > 0
  
  // Filter file changes for feed view
  let filteredChanges = filterAgent === 'all'
    ? fileChanges
    : fileChanges.filter(fc => (fc.agent_id || 'unknown') === filterAgent)
  
  // When in search mode, display search results instead
  if (isSearchMode) {
    filteredChanges = searchResults
  }
  
  const formatChanges = (changes) => {
    if (!changes) return ''
    const { added = 0, removed = 0 } = changes
    // If both are 0, it's a read operation
    if (added === 0 && removed === 0) return 'read'
    return `+${added} -${removed}`
  }

  const performSearch = async () => {
    const query = searchInput.trim()
    if (!query) return
    
    setIsSearching(true)
    setSearchQuery(query)
    
    // Fetch all files from backend
    const response = await fetch('http://localhost:5000/api/files')
    const data = await response.json()
    
    // Filter files by search query
    const queryLower = query.toLowerCase()
    const results = data.files
      .filter(file => file.path.toLowerCase().includes(queryLower))
      .map(file => ({
        file_path: file.path,
        timestamp: new Date(file.modified * 1000).toISOString(),
        agent_id: null,
        changes: null
      }))
    
    setSearchResults(results)
    setIsSearching(false)
    
    // Notify parent component about search mode
    if (onSearchModeChange) {
      onSearchModeChange(true)
    }
  }

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      performSearch()
    }
  }

  const clearSearch = () => {
    setSearchQuery('')
    setSearchInput('')
    setSearchResults([])
    
    // Notify parent component about leaving search mode
    if (onSearchModeChange) {
      onSearchModeChange(false)
    }
  }

  if (filteredChanges.length === 0) {
    return (
      <div className="files-feed">
        <div className="feed-filters">
          <div className="filter-row">
            <label>Filter by Agent:</label>
            <select value={filterAgent} onChange={(e) => setFilterAgent(e.target.value)}>
              {agents.map(agent => (
                <option key={agent} value={agent}>{agent}</option>
              ))}
            </select>
          </div>
          
          <div className="search-row">
            <input
              type="text"
              placeholder="🔍 Search all files (press Enter)..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="search-input"
              disabled={isSearching}
            />
            {isSearchMode && (
              <button onClick={clearSearch} className="back-to-feed-btn">
                ← Back to Feed
              </button>
            )}
          </div>
        </div>
        
        <div className="empty-state">
          <div className="empty-state-icon">📚</div>
          <p>{isSearchMode ? 'No files match your search' : 'No file activity yet'}</p>
          <p style={{ fontSize: '0.9rem', marginTop: '8px' }}>
            {isSearchMode ? 'Try a different search term' : 'Files modified by agents will appear here'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="files-feed">
      <div className="feed-filters">
        <div className="filter-row">
          <label>Filter by Agent:</label>
          <select value={filterAgent} onChange={(e) => setFilterAgent(e.target.value)}>
            {agents.map(agent => (
              <option key={agent} value={agent}>{agent}</option>
            ))}
          </select>
        </div>
        
        <div className="search-row">
          <input
            type="text"
            placeholder="🔍 Search all files (press Enter)..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            className="search-input"
            disabled={isSearching}
          />
          {isSearchMode && (
            <button onClick={clearSearch} className="back-to-feed-btn">
              ← Back to Feed
            </button>
          )}
        </div>
      </div>

      {isSearching && (
        <div className="search-status">
          🔍 Searching all files...
        </div>
      )}

      {isSearchMode && !isSearching && (
        <div className="search-status">
          Found {filteredChanges.length} file{filteredChanges.length !== 1 ? 's' : ''} matching "{searchQuery}"
        </div>
      )}

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

