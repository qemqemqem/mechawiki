import { useState } from 'react'
import './FilesPane.css'
import FilesFeed from './files/FilesFeed'
import FileViewer from './files/FileViewer'

function FilesPane({ fileChanges, selectedFile, onSelectFile }) {
  const handleBackToFeed = () => {
    onSelectFile(null)
  }

  return (
    <div className="pane files-pane">
      <div className="pane-header">
        <h2>
          {selectedFile ? 'Archive' : '📚 Files Feed'}
        </h2>
      </div>

      <div className="pane-content">
        {selectedFile ? (
          <FileViewer
            filePath={selectedFile}
            onBack={handleBackToFeed}
            onNavigate={onSelectFile}
          />
        ) : (
          <FilesFeed
            fileChanges={fileChanges}
            onSelectFile={onSelectFile}
          />
        )}
      </div>
    </div>
  )
}

export default FilesPane

