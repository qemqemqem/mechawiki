import { useState } from 'react'
import './AgentsPane.css'
import CommandCenter from './agents/CommandCenter'
import AgentView from './agents/AgentView'
import NewAgentModal from './agents/NewAgentModal'

function AgentsPane({
  agents,
  selectedAgent,
  onSelectAgent,
  onCreateAgent,
  onPauseAgent,
  onResumeAgent,
  onArchiveAgent,
  onSendMessage
}) {
  const [showNewAgentModal, setShowNewAgentModal] = useState(false)

  const handleBackToCommandCenter = () => {
    onSelectAgent(null)
  }

  return (
    <div className="pane agents-pane">
      <div className="pane-header">
        <h2>
          {selectedAgent ? '⚔️ Agent View' : '🏰 Agents Command Center'}
        </h2>
        {!selectedAgent && (
          <button 
            className="primary"
            onClick={() => setShowNewAgentModal(true)}
          >
            + New Agent
          </button>
        )}
      </div>

      <div className="pane-content">
        {selectedAgent ? (
          <AgentView
            agent={selectedAgent}
            onBack={handleBackToCommandCenter}
            onPause={() => onPauseAgent(selectedAgent.id)}
            onResume={() => onResumeAgent(selectedAgent.id)}
            onArchive={() => onArchiveAgent(selectedAgent.id)}
            onSendMessage={(message) => onSendMessage(selectedAgent.id, message)}
          />
        ) : (
          <CommandCenter
            agents={agents}
            onSelectAgent={onSelectAgent}
            onPauseAgent={onPauseAgent}
            onResumeAgent={onResumeAgent}
            onArchiveAgent={onArchiveAgent}
          />
        )}
      </div>

      {showNewAgentModal && (
        <NewAgentModal
          onClose={() => setShowNewAgentModal(false)}
          onCreate={onCreateAgent}
        />
      )}
    </div>
  )
}

export default AgentsPane

