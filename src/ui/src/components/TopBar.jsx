import './TopBar.css'

function TopBar({ isConnected, sessionCost, exactCost }) {
  // Format exact cost for tooltip
  const tooltip = exactCost !== null && exactCost !== undefined
    ? `Exact: $${exactCost.toFixed(6)}`
    : null

  return (
    <div className="top-bar">
      <div className="top-bar-left">
        <h1 className="app-title">
          Strange Stories from the Dreaming Machine God
        </h1>
      </div>
      
      <div className="top-bar-right">
        {sessionCost !== null && (
          <div className="cost-display" title={tooltip}>
            <span className="cost-icon">💰</span>
            {sessionCost}
          </div>
        )}
        
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot"></span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
    </div>
  )
}

export default TopBar

