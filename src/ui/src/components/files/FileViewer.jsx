import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './FileViewer.css'

function FileViewer({ filePath, onBack, onNavigate }) {
  const [content, setContent] = useState('')
  const [editMode, setEditMode] = useState(false)
  const [editedContent, setEditedContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchFile()
  }, [filePath])

  const fetchFile = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`http://localhost:5000/api/files/${filePath}`)
      if (!response.ok) {
        throw new Error(`Failed to load file: ${response.statusText}`)
      }
      
      const data = await response.json()
      setContent(data.content || '')
      setEditedContent(data.content || '')
      setLoading(false)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/files/${filePath}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: editedContent })
      })
      
      if (!response.ok) {
        throw new Error('Failed to save file')
      }
      
      setContent(editedContent)
      setEditMode(false)
      alert('File saved successfully!')
    } catch (err) {
      alert(`Error saving file: ${err.message}`)
    }
  }

  const handleCancel = () => {
    setEditedContent(content)
    setEditMode(false)
  }

  // Custom link renderer for wiki links
  const renderLink = ({ href, children }) => {
    // Check if it's an internal wiki link
    const isWikiLink = !href.startsWith('http') && !href.startsWith('mailto:')
    
    if (isWikiLink) {
      // Normalize wiki link path
      let targetFile = href
      
      // Handle different link formats
      if (href.startsWith('./')) {
        targetFile = href.slice(2)
      } else if (href.startsWith('/')) {
        targetFile = href.slice(1)
      }
      
      // Ensure .md extension
      if (!targetFile.endsWith('.md')) {
        targetFile = `${targetFile}.md`
      }
      
      // Ensure it's in articles/ if not already specified
      if (!targetFile.startsWith('articles/')) {
        targetFile = `articles/${targetFile}`
      }
      
      return (
        <a
          href="#"
          className="wiki-link"
          onClick={(e) => {
            e.preventDefault()
            onNavigate(targetFile) // Navigate to the linked file
          }}
        >
          {children}
        </a>
      )
    }
    
    // External link
    return (
      <a href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    )
  }

  if (loading) {
    return (
      <div className="file-viewer">
        <div className="file-viewer-header">
          <button onClick={onBack} className="back-button">
            ← Back to Feed
          </button>
        </div>
        <div className="loading-state">Loading file...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="file-viewer">
        <div className="file-viewer-header">
          <button onClick={onBack} className="back-button">
            ← Back to Feed
          </button>
        </div>
        <div className="error-state">
          <p>❌ Error: {error}</p>
          <button onClick={fetchFile}>Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="file-viewer">
      <div className="file-viewer-header">
        <button onClick={onBack} className="back-button">
          ← Back to Feed
        </button>
        
        <h3 className="file-path">{filePath}</h3>
        
        <div className="file-controls">
          {editMode ? (
            <>
              <button onClick={handleSave} className="success">
                💾 Save
              </button>
              <button onClick={handleCancel}>
                Cancel
              </button>
            </>
          ) : (
            <button onClick={() => setEditMode(true)} className="primary">
              ✏️ Edit
            </button>
          )}
        </div>
      </div>

      <div className="file-content">
        {editMode ? (
          <Editor
            height="100%"
            defaultLanguage="markdown"
            value={editedContent}
            onChange={(value) => setEditedContent(value || '')}
            theme="light"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              wordWrap: 'on',
              scrollBeyondLastLine: false
            }}
          />
        ) : (
          <div className="markdown-preview">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: renderLink
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

export default FileViewer

