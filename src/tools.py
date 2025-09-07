"""FastMCP tools for the WikiAgent."""
import os
import re
import toml
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from openai import OpenAI

# Load config
config = toml.load("config.toml")

# Global state for story tracking
class StoryState:
    def __init__(self) -> None:
        self.current_position: int = 0
        self.story_text: str = ""
        self.linked_articles: List[Dict[str, str]] = []  # Track recently linked articles for context
        
    def load_story(self, story_name: str) -> bool:
        """Load story text from file."""
        story_path = Path(config["paths"]["content_dir"]) / story_name / f"{story_name}.txt"
        if story_path.exists():
            with open(story_path, 'r', encoding='utf-8') as f:
                self.story_text = f.read()
            return True
        return False
    
    def get_current_chunk(self, num_words: Optional[int] = None) -> str:
        """Get current story chunk."""
        if not num_words:
            num_words = config["story"]["chunk_size"]
            
        words = self.story_text.split()
        start_word = self.current_position
        end_word = min(start_word + num_words, len(words))
        
        return " ".join(words[start_word:end_word])
    
    def advance_story(self, num_words: int) -> str:
        """Advance story position and return new chunk."""
        # Apply guardrails
        min_advance: int = config["story"]["min_advance"]
        max_advance: int = config["story"]["max_advance"]
        num_words = max(min_advance, min(num_words, max_advance))
        
        old_position = self.current_position
        self.current_position += num_words
        
        # Don't go past end of story
        total_words = len(self.story_text.split())
        if self.current_position >= total_words:
            self.current_position = total_words
            return "END_OF_STORY"
        
        return self.get_current_chunk()

# Initialize story state
story_state = StoryState()

# Initialize FastMCP server
mcp = FastMCP("WikiAgent")

@mcp.tool()
def advance(num_words: Optional[int] = None) -> str:
    """Advance the story by specified number of words and return new chunk.
    
    Args:
        num_words: Number of words to advance (default from config)
    
    Returns:
        The new story chunk or 'END_OF_STORY' if finished
    """
    if not num_words:
        num_words = config["story"]["chunk_size"]
    
    # Load story if not already loaded
    if not story_state.story_text:
        story_name = config["story"]["current_story"]
        if not story_state.load_story(story_name):
            return f"ERROR: Could not load story '{story_name}'"
    
    new_chunk = story_state.advance_story(num_words)
    
    if new_chunk == "END_OF_STORY":
        return "You have reached the end of the story."
    
    return f"Current story position: word {story_state.current_position}\n\n{new_chunk}"

@mcp.tool()
def add_article(title: str, content: str) -> str:
    """Create a new wiki article.
    
    Args:
        title: Article title (will be slugified for filename)
        content: Article content in markdown format
        
    Returns:
        Success message or error
    """
    # Slugify title for filename
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    
    # Create article path
    story_name = config["story"]["current_story"]
    articles_dir = Path(config["paths"]["content_dir"]) / story_name / config["paths"]["articles_dir"]
    articles_dir.mkdir(parents=True, exist_ok=True)
    
    article_path = articles_dir / f"{slug}.md"
    
    # Check if article already exists
    if article_path.exists():
        return f"ERROR: Article '{title}' already exists. Use edit_article() to modify it."
    
    # Write article
    try:
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{content}")
        
        # Track this article as recently linked
        story_state.linked_articles.append({
            'title': title,
            'slug': slug,
            'path': str(article_path)
        })
        
        # Keep only max_linked_articles most recent
        max_articles = config["context"]["max_linked_articles"]
        if len(story_state.linked_articles) > max_articles:
            story_state.linked_articles = story_state.linked_articles[-max_articles:]
        
        return f"Successfully created article: {title} -> {slug}.md"
        
    except Exception as e:
        return f"ERROR: Failed to create article - {str(e)}"

@mcp.tool()
def edit_article(title: str, edit_block: str) -> str:
    """Edit an existing wiki article using Aider-style search/replace blocks.
    
    Args:
        title: Article title to edit
        edit_block: Search/replace block in format:
                   <<<<<<< SEARCH
                   text to find
                   =======
                   text to replace with
                   >>>>>>> REPLACE
        
    Returns:
        Success message or error
    """
    from utils.diffing import apply_search_replace_block
    
    # Slugify title to find file
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    
    # Find article path
    story_name = config["story"]["current_story"]
    articles_dir = Path(config["paths"]["content_dir"]) / story_name / config["paths"]["articles_dir"]
    article_path = articles_dir / f"{slug}.md"
    
    if not article_path.exists():
        return f"ERROR: Article '{title}' does not exist. Use add_article() to create it."
    
    try:
        # Read current content
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply search/replace with retry logic
        result = apply_search_replace_block(content, edit_block, max_retries=2)
        
        if not result.success:
            return f"ERROR: Edit failed for article '{title}' - {result.message}"
        
        # Write back the new content
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(result.new_content)
        
        return f"Successfully edited article '{title}' - {result.message}"
        
    except Exception as e:
        return f"ERROR: Failed to edit article - {str(e)}"

def _generate_image_dalle(art_prompt: str) -> str:
    """Generate image using DALLE-3."""
    client = OpenAI()
    
    response = client.images.generate(
        model="dall-e-3",
        prompt=art_prompt,
        size=config["image"]["size"],
        quality=config["image"]["quality"],
        n=1
    )
    
    return response.data[0].url

def _generate_image_replicate(art_prompt: str) -> str:
    """Generate image using Replicate (placeholder for future implementation)."""
    raise NotImplementedError("Replicate image generation not yet implemented")

def _generate_image_midjourney(art_prompt: str) -> str:
    """Generate image using Midjourney (placeholder for future implementation)."""
    raise NotImplementedError("Midjourney image generation not yet implemented")

@mcp.tool()
def create_image(art_prompt: str) -> str:
    """Generate an image using configured generator and save it to the images directory.
    
    Args:
        art_prompt: Detailed prompt describing the image to generate
        
    Returns:
        Success message with filename or error
    """
    try:
        # Get configured image generator
        generator: str = config["image"]["generator"].lower()
        
        # Generate image based on configured generator
        if generator == "dalle":
            image_url = _generate_image_dalle(art_prompt)
        elif generator == "replicate":
            image_url = _generate_image_replicate(art_prompt)
        elif generator == "midjourney":
            image_url = _generate_image_midjourney(art_prompt)
        else:
            return f"ERROR: Unsupported image generator: {generator}. Supported: dalle, replicate, midjourney"
        
        # Download the image
        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()
        
        # Create filename from prompt (slugified)
        filename_base = re.sub(r'[^\w\s-]', '', art_prompt.lower())
        filename_base = re.sub(r'[-\s]+', '-', filename_base).strip('-')
        filename_base = filename_base[:50]  # Limit length
        
        # Create images directory path
        story_name: str = config["story"]["current_story"]
        images_dir = Path(config["paths"]["content_dir"]) / story_name / config["paths"]["images_dir"]
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Find unique filename
        counter = 1
        while True:
            if counter == 1:
                filename = f"{filename_base}.png"
            else:
                filename = f"{filename_base}-{counter}.png"
                
            image_path = images_dir / filename
            if not image_path.exists():
                break
            counter += 1
        
        # Save image
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        
        return f"Successfully created image using {generator}: {filename}\nPrompt: {art_prompt}\nSaved to: {image_path}"
        
    except Exception as e:
        return f"ERROR: Failed to create image - {str(e)}"

if __name__ == "__main__":
    # Run the MCP server
    mcp.run(transport="stdio")