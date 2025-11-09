"""
Tests for rename_my_story() tool and rename_story_file() utility.
"""
import pytest
import tempfile
import shutil
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.files import rename_story_file, add_to_story
from src.agents.writer_agent import WriterAgent


@pytest.fixture
def temp_wikicontent():
    """Create a temporary wikicontent directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix='test_wikicontent_')
    original_path = os.environ.get('WIKICONTENT_PATH')
    os.environ['WIKICONTENT_PATH'] = temp_dir
    
    yield Path(temp_dir)
    
    # Cleanup
    if original_path:
        os.environ['WIKICONTENT_PATH'] = original_path
    else:
        del os.environ['WIKICONTENT_PATH']
    
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_session():
    """Set a temporary session name for testing."""
    original_session = os.environ.get('SESSION_NAME')
    os.environ['SESSION_NAME'] = 'test_session_rename'
    
    yield 'test_session_rename'
    
    # Restore
    if original_session:
        os.environ['SESSION_NAME'] = original_session
    else:
        del os.environ['SESSION_NAME']


class TestRenameStoryFileUtility:
    """Test the rename_story_file() utility function."""
    
    def test_renames_file_successfully(self, temp_wikicontent):
        """Should rename a story file and preserve content."""
        # Create source file
        source_path = temp_wikicontent / "stories" / "original.md"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("# Original Story\n\nOnce upon a time...")
        
        # Rename
        result = rename_story_file("stories/original.md", "stories/renamed.md")
        
        # Verify result
        assert result["success"] is True
        assert result["old_path"] == "stories/original.md"
        assert result["new_path"] == "stories/renamed.md"
        assert "Renamed story file" in result["message"]
        
        # Verify filesystem
        assert not source_path.exists()
        target_path = temp_wikicontent / "stories" / "renamed.md"
        assert target_path.exists()
        assert "Once upon a time" in target_path.read_text()
    
    def test_creates_target_directory_if_needed(self, temp_wikicontent):
        """Should create target directory structure if it doesn't exist."""
        # Create source file
        source_path = temp_wikicontent / "stories" / "temp.md"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("# Temp\n\nContent here.")
        
        # Rename to new subdirectory
        result = rename_story_file("stories/temp.md", "stories/archive/2025/temp.md")
        
        assert result["success"] is True
        target_path = temp_wikicontent / "stories" / "archive" / "2025" / "temp.md"
        assert target_path.exists()
        assert "Content here" in target_path.read_text()
    
    def test_fails_if_source_not_found(self, temp_wikicontent):
        """Should return error if source file doesn't exist."""
        result = rename_story_file("stories/nonexistent.md", "stories/new.md")
        
        assert result["success"] is False
        assert "Source file not found" in result["error"]
    
    def test_fails_if_target_exists(self, temp_wikicontent):
        """Should return error if target file already exists."""
        # Create both files
        source = temp_wikicontent / "stories" / "source.md"
        target = temp_wikicontent / "stories" / "target.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("Source content")
        target.write_text("Target content")
        
        result = rename_story_file("stories/source.md", "stories/target.md")
        
        assert result["success"] is False
        assert "Target file already exists" in result["error"]
        # Source should still exist
        assert source.exists()
    
    def test_handles_cross_directory_rename(self, temp_wikicontent):
        """Should handle renaming across different directory structures."""
        # Create source in one directory
        source = temp_wikicontent / "drafts" / "story.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# Draft Story\n\nIn progress...")
        
        # Rename to completely different path
        result = rename_story_file("drafts/story.md", "stories/published/final.md")
        
        assert result["success"] is True
        assert not source.exists()
        target = temp_wikicontent / "stories" / "published" / "final.md"
        assert target.exists()
        assert "In progress" in target.read_text()


class TestWriterAgentRenameTool:
    """Test the rename_my_story() tool on WriterAgent."""
    
    def test_agent_has_rename_tool(self, temp_wikicontent, temp_session):
        """WriterAgent should have rename_my_story in its tools."""
        agent = WriterAgent(story_file="stories/test.md", agent_id="writer-001")
        
        tool_names = [t.get('function', {}).get('name') for t in agent.tools]
        assert 'rename_my_story' in tool_names
    
    def test_rename_updates_agent_story_file(self, temp_wikicontent, temp_session):
        """Renaming should update the agent's story_file attribute."""
        # Create agent
        agent = WriterAgent(
            story_file="stories/old_name.md",
            agent_id="writer-001"
        )
        
        # Create the story file
        story_path = temp_wikicontent / agent.story_file
        story_path.parent.mkdir(parents=True, exist_ok=True)
        story_path.write_text("# Old Story\n\nChapter 1...")
        
        # Find rename tool
        rename_tool = None
        for tool in agent.tools:
            if tool.get('function', {}).get('name') == 'rename_my_story':
                rename_tool = tool.get('_function')
                break
        
        assert rename_tool is not None
        
        # Execute rename
        result = rename_tool("new_name.md")
        
        # Verify
        assert result["success"] is True
        assert agent.story_file == "stories/new_name.md"
        assert result["old_file"] == "stories/old_name.md"
        assert result["new_file"] == "stories/new_name.md"
    
    def test_rename_updates_filesystem(self, temp_wikicontent, temp_session):
        """Renaming should move the actual file."""
        agent = WriterAgent(
            story_file="stories/before.md",
            agent_id="writer-002"
        )
        
        # Create file with content
        story_path = temp_wikicontent / agent.story_file
        story_path.parent.mkdir(parents=True, exist_ok=True)
        test_content = "# My Story\n\nThis is important content."
        story_path.write_text(test_content)
        
        # Get rename tool
        rename_tool = next(
            t.get('_function') for t in agent.tools
            if t.get('function', {}).get('name') == 'rename_my_story'
        )
        
        # Rename
        result = rename_tool("after.md")
        
        # Check filesystem
        old_path = temp_wikicontent / "stories" / "before.md"
        new_path = temp_wikicontent / "stories" / "after.md"
        
        assert not old_path.exists()
        assert new_path.exists()
        assert test_content in new_path.read_text()
    
    def test_rename_updates_system_prompt(self, temp_wikicontent, temp_session):
        """Renaming should update the agent's system prompt."""
        agent = WriterAgent(
            story_file="stories/story_v1.md",
            agent_id="writer-003"
        )
        
        # Create file
        story_path = temp_wikicontent / agent.story_file
        story_path.parent.mkdir(parents=True, exist_ok=True)
        story_path.write_text("# Version 1")
        
        # Verify old filename in prompt
        assert "story_v1.md" in agent.system_prompt
        
        # Get rename tool and execute
        rename_tool = next(
            t.get('_function') for t in agent.tools
            if t.get('function', {}).get('name') == 'rename_my_story'
        )
        result = rename_tool("story_v2.md")
        
        # Verify new filename in prompt
        assert result["success"] is True
        assert "story_v2.md" in agent.system_prompt
        assert "story_v1.md" not in agent.system_prompt
    
    def test_rename_keeps_same_directory_if_only_filename(self, temp_wikicontent, temp_session):
        """If only filename is provided, should keep same directory."""
        agent = WriterAgent(
            story_file="stories/drafts/work.md",
            agent_id="writer-004"
        )
        
        # Create file
        story_path = temp_wikicontent / agent.story_file
        story_path.parent.mkdir(parents=True, exist_ok=True)
        story_path.write_text("# Work in Progress")
        
        # Get rename tool
        rename_tool = next(
            t.get('_function') for t in agent.tools
            if t.get('function', {}).get('name') == 'rename_my_story'
        )
        
        # Rename with just filename
        result = rename_tool("final.md")
        
        # Should stay in same directory
        assert result["success"] is True
        assert agent.story_file == "stories/drafts/final.md"
        assert not (temp_wikicontent / "stories" / "drafts" / "work.md").exists()
        assert (temp_wikicontent / "stories" / "drafts" / "final.md").exists()
    
    def test_rename_can_change_directory(self, temp_wikicontent, temp_session):
        """Providing full path should allow changing directories."""
        agent = WriterAgent(
            story_file="stories/drafts/temp.md",
            agent_id="writer-005"
        )
        
        # Create file
        story_path = temp_wikicontent / agent.story_file
        story_path.parent.mkdir(parents=True, exist_ok=True)
        story_path.write_text("# Temporary Draft")
        
        # Get rename tool
        rename_tool = next(
            t.get('_function') for t in agent.tools
            if t.get('function', {}).get('name') == 'rename_my_story'
        )
        
        # Rename with full path to different directory
        result = rename_tool("stories/published/final_version.md")
        
        # Should move to new directory
        assert result["success"] is True
        assert agent.story_file == "stories/published/final_version.md"
        assert (temp_wikicontent / "stories" / "published" / "final_version.md").exists()
    
    def test_rename_fails_gracefully_on_error(self, temp_wikicontent, temp_session):
        """Should return error dict on failure, not raise exception."""
        agent = WriterAgent(
            story_file="stories/nonexistent.md",
            agent_id="writer-006"
        )
        
        # Get rename tool
        rename_tool = next(
            t.get('_function') for t in agent.tools
            if t.get('function', {}).get('name') == 'rename_my_story'
        )
        
        # Try to rename file that doesn't exist
        result = rename_tool("new_name.md")
        
        # Should return error, not crash
        assert result["success"] is False
        assert "error" in result
        assert isinstance(result["error"], str)


class TestRenameToolIntegration:
    """Integration tests for rename tool with other file operations."""
    
    def test_rename_then_add_content(self, temp_wikicontent, temp_session):
        """Should be able to add content after renaming."""
        agent = WriterAgent(
            story_file="stories/story.md",
            agent_id="writer-int-001"
        )
        
        # Create initial file
        story_path = temp_wikicontent / agent.story_file
        story_path.parent.mkdir(parents=True, exist_ok=True)
        story_path.write_text("# Story\n\n")
        
        # Rename
        rename_tool = next(
            t.get('_function') for t in agent.tools
            if t.get('function', {}).get('name') == 'rename_my_story'
        )
        rename_result = rename_tool("epic_tale.md")
        assert rename_result["success"] is True
        
        # Add content to renamed file
        add_result = add_to_story("Chapter 1: The Beginning\n\n", agent.story_file)
        assert add_result["success"] is True
        
        # Verify content was added to new file
        new_path = temp_wikicontent / agent.story_file
        content = new_path.read_text()
        assert "# Story" in content
        assert "Chapter 1: The Beginning" in content

