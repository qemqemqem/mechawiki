import { useState } from 'react'
import './FilesPane.css'
import FilesFeed from './files/FilesFeed'
import FileViewer from './files/FileViewer'

function FilesPane({ fileChanges, selectedFile, onSelectFile }) {
  const [isSearchMode, setIsSearchMode] = useState(false)
  const [articleTitle, setArticleTitle] = useState(null)

  const handleBackToFeed = () => {
    onSelectFile(null)
    setArticleTitle(null)
  }

  const handleSearchModeChange = (inSearchMode) => {
    setIsSearchMode(inSearchMode)
  }

  const handleTitleExtracted = (title) => {
    setArticleTitle(title)
  }

  // Determine pane title
  const getPaneTitle = () => {
    if (selectedFile) {
      // Use extracted article title if available, otherwise fall back to filename
      if (articleTitle) {
        return `📄 ${articleTitle}`
      }
      const fileName = selectedFile.split('/').pop()
      return `📄 ${fileName}`
    }
    if (isSearchMode) {
      return '🔍 Search Results'
    }
    return '📚 Files Feed'
  }

  return (
    <div className="pane files-pane">
      <div className="pane-header">
        <h2>
          {getPaneTitle()}
        </h2>
      </div>

      <div className="pane-content">
        {selectedFile ? (
          <FileViewer
            filePath={selectedFile}
            onBack={handleBackToFeed}
            onNavigate={onSelectFile}
            onTitleExtracted={handleTitleExtracted}
          />
        ) : (
          <FilesFeed
            fileChanges={fileChanges}
            onSelectFile={onSelectFile}
            onSearchModeChange={handleSearchModeChange}
          />
        )}
      </div>
    </div>
  )
}

export default FilesPane

