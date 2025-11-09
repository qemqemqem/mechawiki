import { useState, useEffect } from 'react'
import './NewAgentModal.css'

function NewAgentModal({ onClose, onCreate, agents = [] }) {
  const [type, setType] = useState('ReaderAgent')
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [description, setDescription] = useState('')
  const [config, setConfig] = useState({})
  const [nameManuallyEdited, setNameManuallyEdited] = useState(false)
  const [slugManuallyEdited, setSlugManuallyEdited] = useState(false)

  // Helper function to convert type to readable name
  const typeToName = (agentType) => {
    const typeMap = {
      'ReaderAgent': 'Reader Agent',
      'WriterAgent': 'Writer Agent',
      'InteractiveAgent': 'Interactive Agent'
    }
    return typeMap[agentType] || agentType
  }

  // Helper function to convert name to slug format
  const nameToSlug = (agentName) => {
    return agentName
      .toLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9-]/g, '')
  }

  // Helper function to find the first available number for a slug
  const findFirstAvailableNumber = (baseSlug) => {
    const existingSlugs = agents.map(agent => agent.id || '')
    
    for (let num = 1; num <= 999; num++) {
      const paddedNum = num.toString().padStart(3, '0')
      const testSlug = `${baseSlug}-${paddedNum}`
      
      if (!existingSlugs.includes(testSlug)) {
        return paddedNum
      }
    }
    
    return '999'
  }

  // Auto-populate name when type changes
  useEffect(() => {
    if (!nameManuallyEdited) {
      const baseName = typeToName(type)
      const baseSlug = nameToSlug(baseName)
      const number = findFirstAvailableNumber(baseSlug)
      setName(`${baseName} ${number}`)
    }
  }, [type, nameManuallyEdited, agents])

  // Auto-populate slug when name changes
  useEffect(() => {
    if (!slugManuallyEdited) {
      const slugBase = nameToSlug(name)
      setSlug(slugBase)
    }
  }, [name, slugManuallyEdited])

  const handleNameChange = (e) => {
    setName(e.target.value)
    setNameManuallyEdited(true)
  }

  const handleSlugChange = (e) => {
    setSlug(e.target.value)
    setSlugManuallyEdited(true)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!name.trim()) {
      alert('Please enter an agent name')
      return
    }

    if (!slug.trim()) {
      alert('Please enter a slug')
      return
    }

    // Check if slug already exists
    const existingSlugs = agents.map(agent => agent.id || '')
    if (existingSlugs.includes(slug)) {
      alert('This slug is already in use. Please choose a different one.')
      return
    }
    
    onCreate({
      id: slug,
      name: name.trim(),
      type,
      config: {
        ...config,
        description: description.trim()
      }
    })
    
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>⚔️ Create New Agent</h2>
          <button onClick={onClose} className="close-button">×</button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="agent-type">Agent Type</label>
            <select
              id="agent-type"
              value={type}
              onChange={(e) => setType(e.target.value)}
              autoFocus
            >
              <option value="ReaderAgent">Reader Agent</option>
              <option value="WriterAgent">Writer Agent</option>
              <option value="InteractiveAgent">Interactive Agent</option>
            </select>
            <p className="help-text">
              {type === 'ReaderAgent' && 'Reads stories and creates wiki content'}
              {type === 'WriterAgent' && 'Writes stories from wiki content'}
              {type === 'InteractiveAgent' && 'Creates interactive RPG experiences'}
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="agent-name">Agent Name</label>
            <input
              id="agent-name"
              type="text"
              value={name}
              onChange={handleNameChange}
              placeholder="e.g., Reader Agent 001"
            />
          </div>

          <div className="form-group">
            <label htmlFor="agent-slug">Agent Slug (ID)</label>
            <input
              id="agent-slug"
              type="text"
              value={slug}
              onChange={handleSlugChange}
              placeholder="e.g., reader-agent-001"
            />
            <p className="help-text">
              Auto-generated from name. This will be the agent's unique identifier.
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="agent-description">Agent Description</label>
            <textarea
              id="agent-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe this agent's purpose, goals, or special instructions..."
              rows={4}
            />
            <p className="help-text">
              Optional: Add notes about this agent's purpose. These will be included in its system prompt.
            </p>
          </div>

          <div className="modal-actions">
            <button type="button" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="primary">
              Create Agent
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default NewAgentModal

