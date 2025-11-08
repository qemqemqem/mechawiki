import './TopBar.css'

function TopBar({ isConnected }) {
  return (
    <div className="top-bar">
      <div className="top-bar-left">
        <h1 className="app-title">
          <span className="title-icon">🏰</span>
          MechaWiki
        </h1>
      </div>
      
      <div className="top-bar-right">
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot"></span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
    </div>
  )
}

export default TopBar

