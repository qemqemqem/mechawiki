import { formatDistanceToNow } from '../../utils/time'
import './CommandCenter.css'

function CommandCenter({ agents, onSelectAgent, onPauseAgent, onResumeAgent, onArchiveAgent }) {
  
  const getStatusIcon = (status) => {
    switch(status) {
      case 'running':
        return '●' // Solid circle
      case 'waiting_for_input':
        return '◉' // Circle with dot
      case 'paused':
        return '◐' // Half circle
      case 'stopped':
      case 'archived':
        return '○' // Empty circle
      default:
        return '○'
    }
  }

  const getStatusClass = (status) => {
    switch(status) {
      case 'running':
        return 'status-running'
      case 'waiting_for_input':
        return 'status-waiting'
      case 'paused':
        return 'status-paused'
      default:
        return 'status-stopped'
    }
  }

  const getStatusLabel = (status) => {
    switch(status) {
      case 'running':
        return 'Running'
      case 'waiting_for_input':
        return 'Waiting for input'
      case 'paused':
        return 'Paused by user'
      case 'stopped':
        return 'Stopped'
      case 'archived':
        return 'Archived'
      default:
        return 'Unknown'
    }
  }

  if (agents.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🏰</div>
        <p>No agents yet</p>
        <p style={{ fontSize: '0.9rem', marginTop: '8px' }}>
          Click "+ New Agent" to create your first agent
        </p>
      </div>
    )
  }

  return (
    <div className="command-center">
      <div className="agents-list">
        {agents.map(agent => (
          <div
            key={agent.id}
            className="card agent-card"
            onClick={() => onSelectAgent(agent)}
          >
            <div className="agent-card-header">
              <span className={`status-indicator ${getStatusClass(agent.status)}`}>
                {getStatusIcon(agent.status)}
              </span>
              <span className="agent-name">{agent.name}</span>
              
              <div className="agent-controls" onClick={(e) => e.stopPropagation()}>
                {agent.status === 'running' && (
                  <button
                    onClick={() => onPauseAgent(agent.id)}
                    title="Pause"
                  >
                    ⏸
                  </button>
                )}
                {(agent.status === 'paused' || agent.status === 'waiting_for_input') && (
                  <button
                    onClick={() => onResumeAgent(agent.id)}
                    title="Resume"
                  >
                    ▶
                  </button>
                )}
                <button
                  onClick={() => onArchiveAgent(agent.id)}
                  title="Archive"
                >
                  📦
                </button>
              </div>
            </div>

            <div className="agent-meta">
              {agent.type} • {getStatusLabel(agent.status)}
            </div>

            {agent.last_action && (
              <div className="agent-last-action">
                Last: {agent.last_action}
              </div>
            )}

            {agent.last_action_time && (
              <div className="agent-timestamp">
                {formatDistanceToNow(agent.last_action_time)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default CommandCenter

