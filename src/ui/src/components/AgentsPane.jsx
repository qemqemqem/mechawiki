import { useState } from 'react'
import './AgentsPane.css'
import CommandCenter from './agents/CommandCenter'
import AgentView from './agents/AgentView'
import NewAgentModal from './agents/NewAgentModal'

function AgentsPane({
  agents,
  selectedAgentId,
  onSelectAgent,
  onCreateAgent,
  onPauseAgent,
  onResumeAgent,
  onArchiveAgent,
  onPauseAll,
  onResumeAll,
  onSendMessage
}) {
  const [showNewAgentModal, setShowNewAgentModal] = useState(false)

  // Look up the selected agent from the agents array
  const selectedAgent = selectedAgentId 
    ? agents.find(agent => agent.id === selectedAgentId)
    : null

  const handleBackToCommandCenter = () => {
    onSelectAgent(null)
  }

  return (
    <div className="pane agents-pane">
      <div className="pane-header">
        <h2>
          {selectedAgent ? `⚔️ ${selectedAgent.name}` : 'Command Center'}
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
            onPauseAll={onPauseAll}
            onResumeAll={onResumeAll}
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

