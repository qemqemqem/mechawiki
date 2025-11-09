import { useState } from 'react'
import './NewAgentModal.css'

function NewAgentModal({ onClose, onCreate }) {
  const [name, setName] = useState('')
  const [type, setType] = useState('ReaderAgent')
  const [description, setDescription] = useState('')
  const [config, setConfig] = useState({})

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!name.trim()) {
      alert('Please enter an agent name')
      return
    }
    
    onCreate({
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
            <label htmlFor="agent-name">Agent Name</label>
            <input
              id="agent-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Reader Agent 1"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="agent-type">Agent Type</label>
            <select
              id="agent-type"
              value={type}
              onChange={(e) => setType(e.target.value)}
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

