import { useState, useEffect } from 'react'
import './App.css'
import TopBar from './components/TopBar'
import AgentsPane from './components/AgentsPane'
import FilesPane from './components/FilesPane'

function App() {
  const [agents, setAgents] = useState([])
  const [selectedAgentId, setSelectedAgentId] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileChanges, setFileChanges] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [leftPaneWidth, setLeftPaneWidth] = useState(50) // Percentage
  const [isResizing, setIsResizing] = useState(false)

  // Fetch agents and initial files on mount
  useEffect(() => {
    fetchAgents()
    fetchInitialFiles()
    connectToFileFeed()
  }, [])

  // Handle resize drag
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return
      
      const newWidth = (e.clientX / window.innerWidth) * 100
      // Constrain between 20% and 80%
      const constrainedWidth = Math.max(20, Math.min(80, newWidth))
      setLeftPaneWidth(constrainedWidth)
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    } else {
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  const fetchAgents = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/agents')
      const data = await response.json()
      setAgents(data.agents || [])
      setIsConnected(true)
    } catch (error) {
      console.error('Error fetching agents:', error)
      setIsConnected(false)
    }
  }

  const fetchInitialFiles = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/files')
      const data = await response.json()
      const articleFiles = (data.files || []).filter(f => 
        f.path.startsWith('articles/') && f.path.endsWith('.md')
      )
      
      // Pick 5 random files
      const shuffled = articleFiles.sort(() => 0.5 - Math.random())
      const selected = shuffled.slice(0, 5)
      
      // Create initial file change entries
      const initialChanges = selected.map(file => ({
        type: 'file_changed',
        agent_id: 'system',
        file_path: file.path,
        action: 'initial',
        changes: { added: 0, removed: 0 },
        timestamp: new Date(file.modified * 1000).toISOString()
      }))
      
      setFileChanges(initialChanges)
    } catch (error) {
      console.error('Error fetching initial files:', error)
    }
  }

  const connectToFileFeed = () => {
    const eventSource = new EventSource('http://localhost:5000/api/files/feed')
    
    eventSource.onopen = () => {
      console.log('📡 Connected to file feed')
      setIsConnected(true)
    }
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'file_changed') {
          setFileChanges(prev => [data, ...prev])
        }
      } catch (error) {
        // Ignore keepalive messages
      }
    }
    
    eventSource.onerror = () => {
      console.error('❌ File feed connection error')
      setIsConnected(false)
      eventSource.close()
      
      // Reconnect after 5 seconds
      setTimeout(connectToFileFeed, 5000)
    }
    
    return () => eventSource.close()
  }

  const handleCreateAgent = async (agentData) => {
    try {
      const response = await fetch('http://localhost:5000/api/agents/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(agentData)
      })
      
      if (response.ok) {
        await fetchAgents()
      }
    } catch (error) {
      console.error('Error creating agent:', error)
    }
  }

  const handlePauseAgent = async (agentId) => {
    try {
      await fetch(`http://localhost:5000/api/agents/${agentId}/pause`, {
        method: 'POST'
      })
      await fetchAgents()
    } catch (error) {
      console.error('Error pausing agent:', error)
    }
  }

  const handleResumeAgent = async (agentId) => {
    try {
      await fetch(`http://localhost:5000/api/agents/${agentId}/resume`, {
        method: 'POST'
      })
      await fetchAgents()
    } catch (error) {
      console.error('Error resuming agent:', error)
    }
  }

  const handleArchiveAgent = async (agentId) => {
    try {
      await fetch(`http://localhost:5000/api/agents/${agentId}/archive`, {
        method: 'POST'
      })
      await fetchAgents()
    } catch (error) {
      console.error('Error archiving agent:', error)
    }
  }

  const handlePauseAll = async () => {
    try {
      await fetch('http://localhost:5000/api/agents/pause-all', {
        method: 'POST'
      })
      await fetchAgents()
    } catch (error) {
      console.error('Error pausing all agents:', error)
    }
  }

  const handleResumeAll = async () => {
    try {
      await fetch('http://localhost:5000/api/agents/resume-all', {
        method: 'POST'
      })
      await fetchAgents()
    } catch (error) {
      console.error('Error resuming all agents:', error)
    }
  }

  const handleSendMessage = async (agentId, message) => {
    try {
      await fetch(`http://localhost:5000/api/agents/${agentId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      })
    } catch (error) {
      console.error('Error sending message:', error)
    }
  }

  return (
    <div className="app">
      <TopBar isConnected={isConnected} />
      
      <div className="app-content">
        <div 
          className="agents-pane-wrapper"
          style={{ width: `${leftPaneWidth}%` }}
        >
          <AgentsPane
            agents={agents}
            selectedAgentId={selectedAgentId}
            onSelectAgent={(agent) => setSelectedAgentId(agent?.id || null)}
            onCreateAgent={handleCreateAgent}
            onPauseAgent={handlePauseAgent}
            onResumeAgent={handleResumeAgent}
            onArchiveAgent={handleArchiveAgent}
            onPauseAll={handlePauseAll}
            onResumeAll={handleResumeAll}
            onSendMessage={handleSendMessage}
          />
        </div>
        
        <div 
          className="resize-handle"
          onMouseDown={() => setIsResizing(true)}
        />
        
        <div 
          className="files-pane-wrapper"
          style={{ width: `${100 - leftPaneWidth}%` }}
        >
          <FilesPane
            fileChanges={fileChanges}
            selectedFile={selectedFile}
            onSelectFile={setSelectedFile}
          />
      </div>
      </div>
    </div>
  )
}

export default App
