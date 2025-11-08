import { useState, useEffect } from 'react'
import './App.css'
import TopBar from './components/TopBar'
import AgentsPane from './components/AgentsPane'
import FilesPane from './components/FilesPane'

function App() {
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileChanges, setFileChanges] = useState([])
  const [isConnected, setIsConnected] = useState(false)

  // Fetch agents on mount
  useEffect(() => {
    fetchAgents()
    
    // Connect to file feed
    connectToFileFeed()
  }, [])

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
        <AgentsPane
          agents={agents}
          selectedAgent={selectedAgent}
          onSelectAgent={setSelectedAgent}
          onCreateAgent={handleCreateAgent}
          onPauseAgent={handlePauseAgent}
          onResumeAgent={handleResumeAgent}
          onArchiveAgent={handleArchiveAgent}
          onSendMessage={handleSendMessage}
        />
        
        <div className="resize-handle" />
        
        <FilesPane
          fileChanges={fileChanges}
          selectedFile={selectedFile}
          onSelectFile={setSelectedFile}
        />
      </div>
    </div>
  )
}

export default App
