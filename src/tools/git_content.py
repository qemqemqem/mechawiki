"""
Git content management tool using GitPython.

Text-only git repositories for story content:
- story.log: Original story text
- *.md: Generated markdown content with media references
- No binary files - only text IDs referencing external media system
"""
from pathlib import Path
from typing import Optional
import git
from git import Repo


class GitContentTool:
    """
    Text-only git content management tool.

    Manages story content in git with text references to external media.
    """

    def __init__(self, repo_path: str, session_id: str = "main"):
        """
        Initialize git content tool.

        Args:
            repo_path: Path to the git repository
            session_id: Branch name for this session
        """
        self.repo_path = Path(repo_path)
        self.session_id = session_id

        # Initialize or open repository
        if self.repo_path.exists() and (self.repo_path / ".git").exists():
            self.repo = Repo(self.repo_path)
        else:
            self.repo_path.mkdir(parents=True, exist_ok=True)
            self.repo = Repo.init(self.repo_path)
            self._setup_initial_structure()

        # Switch to session branch
        self._checkout_branch(session_id)

    def _setup_initial_structure(self):
        """Set up initial repository structure."""
        # Create empty story.log
        (self.repo_path / "story.log").write_text("", encoding='utf-8')

        # Create README explaining structure
        readme_content = """# Story Repository

This repository contains text-only content for a story:

- `story.log`: Original story text
- `*.md`: Generated markdown content
- Media references use text IDs that point to external media system

No binary files are stored in this repository.
"""
        (self.repo_path / "README.md").write_text(readme_content, encoding='utf-8')

        # Create .gitignore for text-only policy
        gitignore_content = """# Binary files not allowed
*.jpg
*.jpeg
*.png
*.gif
*.webp
*.mp4
*.mp3
*.wav

# Temporary files
*.tmp
*.temp
.DS_Store
Thumbs.db
"""
        (self.repo_path / ".gitignore").write_text(gitignore_content, encoding='utf-8')

        # Initial commit
        self.repo.index.add(["."])
        self.repo.index.commit("Initial repository setup")

    def _checkout_branch(self, branch_name: str):
        """Checkout or create a branch."""
        try:
            if branch_name in [b.name for b in self.repo.branches]:
                self.repo.git.checkout(branch_name)
            else:
                self.repo.git.checkout('-b', branch_name)
        except git.exc.GitCommandError:
            # Handle case where repo has no commits yet
            pass

    def load_story_text(self) -> str:
        """Load story text from story.log."""
        story_path = self.repo_path / "story.log"
        if story_path.exists():
            return story_path.read_text(encoding='utf-8')
        return ""

    def save_story_text(self, content: str, position: int, message: Optional[str] = None):
        """
        Save story text and commit changes.

        Args:
            content: Story text content
            position: Word position that triggered the save
            message: Custom commit message
        """
        story_path = self.repo_path / "story.log"
        story_path.write_text(content, encoding='utf-8')

        # Commit changes
        self.repo.index.add(["story.log"])
        commit_msg = message or f"Update story at position {position}"
        self.repo.index.commit(commit_msg)

    def save_markdown_content(self, filename: str, content: str, position: int):
        """
        Save markdown content file and commit.

        Args:
            filename: Name of the markdown file (without .md extension)
            content: Markdown content (may include media ID references)
            position: Word position that triggered generation
        """
        if not filename.endswith('.md'):
            filename += '.md'

        file_path = self.repo_path / filename
        file_path.write_text(content, encoding='utf-8')

        # Commit changes
        self.repo.index.add([filename])
        self.repo.index.commit(f"Generate {filename} at position {position}")

    def get_file_path(self, filename: str) -> Path:
        """Get full path to a file in the repository."""
        return self.repo_path / filename

    def migrate_from_file(self, source_file: Path):
        """
        Migrate existing story file into git repository.

        Args:
            source_file: Path to existing story file
        """
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")

        # Copy content to story.log
        content = source_file.read_text(encoding='utf-8')
        self.save_story_text(content, 0, f"Migrate from {source_file.name}")

    def get_commit_log(self, max_count: int = 10) -> list:
        """Get recent commit history."""
        try:
            commits = list(self.repo.iter_commits(max_count=max_count))
            return [f"{c.hexsha[:7]} {c.summary}" for c in commits]
        except git.exc.GitCommandError:
            return []

    def list_branches(self) -> list:
        """List all branches."""
        return [branch.name for branch in self.repo.branches]

    def get_current_branch(self) -> str:
        """Get current branch name."""
        try:
            return self.repo.active_branch.name
        except TypeError:
            return "main"