"""FastMCP tools for the WikiAgent."""
import os
import re
import toml
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Annotated
from fastmcp import FastMCP
from openai import OpenAI
from langgraph.types import Command
from langgraph.prebuilt import InjectedState

# Load config
config = toml.load("config.toml")

# Define the WikiAgent state schema (this must match what's used in agent.py)
from typing import TypedDict
from langgraph.graph.message import add_messages

class WikiAgentState(TypedDict):
    """State schema for WikiAgent - must match the one used in agent.py"""
    messages: Annotated[list, add_messages]
    remaining_steps: int  # Required by create_react_agent
    story_info: Dict[str, Any]  # Contains position, text, complete status
    linked_articles: List[Dict[str, str]]

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
                self.story_text = f.read() + "\n\nEND_OF_STORY"
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
        
        # Get the chunk from current position BEFORE advancing
        chunk = self.get_current_chunk(num_words)
        
        # Advance the position
        self.current_position += num_words
        
        # Clamp position to not exceed story length (no special handling needed, END_OF_STORY is in the text)
        total_words = len(self.story_text.split())
        if self.current_position >= total_words:
            self.current_position = total_words
        
        return chunk
    
    def is_story_complete(self) -> bool:
        """Check if we've reached the end of the story."""
        if not self.story_text:
            return False
        words = self.story_text.split()
        return self.current_position >= len(words)
    
    def get_article_context(self) -> str:
        """Get context of currently loaded articles with associated media."""
        if not self.linked_articles:
            return "No articles currently in context."
        
        context = "📚 Articles currently in context:\n"
        for article in self.linked_articles:
            context += f"\n• {article['title']} ({article['slug']}.md)\n"
            
            # Check for associated image
            image_info = self._check_associated_image(article['title'], article['slug'])
            context += f"  Image: {image_info}\n"
            
            # Check for associated song
            song_info = self._check_associated_song(article['title'], article['slug'])
            context += f"  Song: {song_info}\n"
        
        return context
    
    def _check_associated_image(self, title: str, slug: str) -> str:
        """Check if an image exists for this article."""
        story_name = config["story"]["current_story"]
        images_dir = Path(config["paths"]["content_dir"]) / story_name / config["paths"]["images_dir"]
        
        # Common image extensions
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            image_path = images_dir / f"{slug}{ext}"
            if image_path.exists():
                return f"{slug}{ext}"
        
        return f"no image exists for {title}"
    
    def _check_associated_song(self, title: str, slug: str) -> str:
        """Check if a song exists for this article."""
        story_name = config["story"]["current_story"]
        songs_dir = Path(config["paths"]["content_dir"]) / story_name / config["paths"]["songs_dir"]
        
        # Common audio extensions
        for ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            song_path = songs_dir / f"{slug}{ext}"
            if song_path.exists():
                return f"{slug}{ext}"
        
        return f"no song exists for {title}"
    
    def load_article_to_context(self, title: str, slug: str, path: str) -> bool:
        """Load an article into context if it exists."""
        article_path = Path(path)
        if not article_path.exists():
            return False
        
        # Check if already in context
        for article in self.linked_articles:
            if article['slug'] == slug:
                return True  # Already loaded
        
        # Add to context
        self.linked_articles.append({
            'title': title,
            'slug': slug,
            'path': path
        })
        
        # Keep only max_linked_articles most recent
        max_articles = config["context"]["max_linked_articles"]
        if len(self.linked_articles) > max_articles:
            self.linked_articles = self.linked_articles[-max_articles:]
        
        return True
    
    def find_existing_article(self, title: str) -> Optional[Dict[str, str]]:
        """Find if an article exists on disk and return its info."""
        # Slugify title to find file
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        
        # Find article path
        story_name = config["story"]["current_story"]
        articles_dir = Path(config["paths"]["content_dir"]) / story_name / config["paths"]["articles_dir"]
        article_path = articles_dir / f"{slug}.md"
        
        if article_path.exists():
            return {
                'title': title,
                'slug': slug,
                'path': str(article_path)
            }
        return None

# Initialize story state and load the current story
story_state = StoryState()
current_story = config["story"]["current_story"]
if not story_state.load_story(current_story):
    print(f"❌ Warning: Could not load story '{current_story}'")
else:
    print(f"✅ Loaded story: {current_story} ({len(story_state.story_text)} characters)")
    print(f"📊 Total words: {len(story_state.story_text.split())}")
    print(f"📍 Initial position: {story_state.current_position}")

# Initialize FastMCP server
mcp = FastMCP("WikiAgent")

@mcp.tool()
def advance(
    num_words: Optional[int] = None,
    state: Annotated[WikiAgentState, InjectedState] = None
) -> Command:
    """Navigate through the story by advancing or rewinding by specified words.
    
    IMPORTANT: This tool controls your reading position in the story text. Unlike typical tools,
    this changes your current location and affects what content you can see. You maintain a 
    single "reading position" that moves forward or backward through the story.
    
    USAGE GUIDANCE:
    - Only advance when you've thoroughly processed the current content
    - Create wiki articles for all notable elements before moving forward
    - You can rewind (negative numbers) to revisit earlier sections if needed
    - Each call shows you a new chunk of text from your new position
    - Your reading position persists between tool calls
    
    Use this tool to move through the story text and get new content to analyze.
    Supports both forward movement (positive numbers) and backward movement (negative numbers).
    
    Args:
        num_words: Number of words to advance. Range: -2000 to +2000. 
                  Positive advances forward, negative rewinds backward.
                  If not provided, uses default chunk size from config (1000).
                  
                  Examples:
                  - advance() -> moves forward 1000 words (default)
                  - advance(500) -> moves forward 500 words  
                  - advance(-300) -> rewinds backward 300 words
    
    Returns:
        Command object with updated story state and current chunk content.
    """
    # Handle default parameter explicitly  
    if num_words is None or num_words == 0:
        num_words = config["story"]["chunk_size"]
    
    # Get or initialize story info from state
    story_info = state.get("story_info", {}) if state else {}
    
    # Load story if needed
    if not story_info:
        story_name = config["story"]["current_story"]
        story_path = Path(config["paths"]["content_dir"]) / story_name / f"{story_name}.txt"
        
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                text = f.read() + "\n\nEND_OF_STORY"
            
            story_info = {
                "name": story_name,
                "text": text,
                "position": 0,
                "total_words": len(text.split()),
                "complete": False
            }
            _log_tool_call("advance", {"num_words": num_words}, f"Loaded story: {story_name}")
        except Exception as e:
            error_msg = f"ERROR: Could not load story '{story_name}': {e}"
            _log_tool_call("advance", {"num_words": num_words}, error_msg)
            return Command(resume=error_msg)
    
    # Apply guardrails
    min_adv = config["story"]["min_advance"]
    max_adv = config["story"]["max_advance"]
    num_words = max(min_adv, min(num_words, max_adv))
    
    # Get current position and calculate chunk
    current_pos = story_info.get("position", 0)
    words = story_info["text"].split()
    
    # Get chunk from current position
    chunk_size = config["story"]["chunk_size"]
    start_pos = current_pos
    end_pos = min(start_pos + chunk_size, len(words))
    chunk = " ".join(words[start_pos:end_pos])
    
    # Apply guardrails and calculate new position (AFTER getting chunk)
    new_pos = max(0, min(current_pos + num_words, len(words)))
    
    # Update story info with new position
    story_info.update({
        "position": new_pos,
        "complete": new_pos >= story_info["total_words"]
    })
    
    # Log current context
    linked_articles = state.get("linked_articles", []) if state else []
    if linked_articles:
        context_log = f"\n{'='*50}\n📚 ARTICLES IN CONTEXT ({len(linked_articles)})\n{'='*50}\n"
        for article in linked_articles:
            context_log += f"  • {article['title']} ({article['slug']}.md)\n"
        context_log += f"{'='*50}\n"
    else:
        context_log = f"\n{'='*50}\n📚 NO ARTICLES IN CONTEXT YET\n{'='*50}\n"
    
    print(context_log, flush=True)
    import sys
    print(context_log, file=sys.stderr, flush=True)
    
    # Prepare result message
    chunk_words = len(chunk.split()) if chunk.strip() else 0
    result_content = f"Showing words {start_pos} - {end_pos} ({chunk_words} words)\n\n{chunk}"
    
    _log_tool_call("advance", {"num_words": num_words}, result_content)
    
    return Command(
        update={"story_info": story_info},
        resume=result_content
    )

@mcp.tool()
def add_article(
    title: str, 
    content: str,
    state: Annotated[WikiAgentState, InjectedState] = None
) -> Command:
    """Create a new wiki-style article for story elements like characters, locations, objects.
    
    Use this tool to document any notable story element that merits a wiki page.
    Articles are saved as markdown files with auto-generated filenames.
    
    Args:
        title: Article title as it will appear in the wiki. Special characters will be
               removed and spaces converted to hyphens for the filename (e.g., "King Arthur" -> "king-arthur.md").
        content: Full article content in markdown format. Should include detailed descriptions,
                story context, and cross-references using wiki-style linking.
                
                WIKI LINKING - USE PROLIFICALLY:
                Link to other articles using [Display Text](./filename.md) syntax:
                - Characters: [Lord Dunsany](./lord-dunsany.md)
                - Locations: [London](./london.md) 
                - Objects: [Magic Sword](./magic-sword.md)
                - Concepts: [Time Travel](./time-travel.md)
                
                LINKING GUIDELINES:
                - Link liberally - every mention of another entity should be a link
                - Use descriptive link text, not just the filename
                - Link to articles that might exist, even if you haven't created them yet
                - Create interconnected web of articles like Wikipedia
                - Link multiple times in long articles for different mentions
                
                DUPLICATE PREVENTION:
                - Cannot create articles with identical titles (case-insensitive)
                - If article exists, you must use edit_article() instead
                - Different titles that generate the same filename will conflict
        
    Returns:
        Success message with generated filename, or ERROR message if article already exists
        or file creation fails.
    """
    # Slugify title for filename
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    
    # Create article path
    story_name = config["story"]["current_story"]
    articles_dir = Path(config["paths"]["content_dir"]) / story_name / config["paths"]["articles_dir"]
    articles_dir.mkdir(parents=True, exist_ok=True)
    
    article_path = articles_dir / f"{slug}.md"
    
    # Get current linked articles from state
    linked_articles = list(state.get("linked_articles", [])) if state else []
    
    # Check if article already exists
    if article_path.exists():
        # Add to linked articles if not already there
        article_info = {'title': title, 'slug': slug, 'path': str(article_path)}
        if not any(a['slug'] == slug for a in linked_articles):
            linked_articles.append(article_info)
        
        # Keep only max_linked_articles most recent
        max_articles = config["context"]["max_linked_articles"]
        if len(linked_articles) > max_articles:
            linked_articles = linked_articles[-max_articles:]
        
        # Build context info
        context_info = "📚 Articles currently in context:\n"
        for article in linked_articles:
            context_info += f"\n• {article['title']} ({article['slug']}.md)\n"
            # Check for associated media
            context_info += f"  Image: no image exists for {article['title']}\n"  # Simplified for now
            context_info += f"  Song: no song exists for {article['title']}\n"
        
        error_msg = f"ERROR: Article '{title}' already exists and has been loaded into context. Use edit_article() to modify it.\n\n{context_info}\n\nPlease try your operation again now that the article is in context."
        _log_tool_call("add_article", {"title": title, "content": content}, error_msg)
        
        return Command(
            update={"linked_articles": linked_articles},
            resume=error_msg
        )
    
    # Write article
    try:
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{content}")
        
        # Add this article to linked articles
        article_info = {'title': title, 'slug': slug, 'path': str(article_path)}
        linked_articles.append(article_info)
        
        # Keep only max_linked_articles most recent
        max_articles = config["context"]["max_linked_articles"]
        if len(linked_articles) > max_articles:
            linked_articles = linked_articles[-max_articles:]
        
        result = f"Successfully created article: {title} -> {slug}.md"
        _log_tool_call("add_article", {"title": title, "content": content}, result)
        
        return Command(
            update={"linked_articles": linked_articles},
            resume=result
        )
        
    except Exception as e:
        error_msg = f"ERROR: Failed to create article - {str(e)}"
        _log_tool_call("add_article", {"title": title, "content": content}, error_msg)
        
        return Command(
            resume=error_msg
        )

@mcp.tool()
def edit_article(
    title: str, 
    edit_block: str,
    state: Annotated[WikiAgentState, InjectedState] = None
) -> Command:
    """Update existing wiki articles using precise search/replace operations.
    
    Use this tool to modify articles when you learn new information about characters,
    locations, or other story elements. Supports fuzzy matching for whitespace differences.
    
    Args:
        title: Exact title of the article to edit (must match existing article).
        edit_block: Aider-style search/replace block with exact format:
                   <<<<<<< SEARCH
                   exact text to find and replace
                   =======
                   new text to replace it with
                   >>>>>>> REPLACE
                   
                   WIKI LINKING IN EDITS - USE PROLIFICALLY:
                   When adding content, include extensive links using [Display Text](./filename.md):
                   - Link every mention of characters, locations, objects, concepts
                   - Create interconnected web of articles like Wikipedia
                   - Use descriptive link text that flows naturally in sentences
                   - Link to articles that might exist, even if not created yet
                   - Multiple links per article are encouraged for comprehensiveness
                   
                   IMPORTANT MATCHING RULES:
                   - First tries exact string match for precision
                   - If that fails, tries "normalized whitespace" matching where:
                     * Leading/trailing spaces on each line are removed
                     * Empty lines are ignored
                     * Multiple consecutive spaces become single spaces
                   - If multiple exact matches exist, edit fails (make search text more specific)
                   - Search text cannot be empty or identical to replace text
        
    Returns:
        Success message indicating edit was applied, or ERROR message if:
        - Article doesn't exist (use add_article to create new ones)
        - Search text not found in article
        - Edit block format is invalid
        - File write operation fails
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
        error_msg = f"ERROR: Article '{title}' does not exist. Use add_article() to create it."
        _log_tool_call("edit_article", {"title": title, "edit_block": edit_block}, error_msg)
        return Command(resume=error_msg)
    
    # Get current linked articles from state and add this article if not already there
    linked_articles = list(state.get("linked_articles", [])) if state else []
    article_info = {'title': title, 'slug': slug, 'path': str(article_path)}
    if not any(a['slug'] == slug for a in linked_articles):
        linked_articles.append(article_info)
        
        # Keep only max_linked_articles most recent
        max_articles = config["context"]["max_linked_articles"]
        if len(linked_articles) > max_articles:
            linked_articles = linked_articles[-max_articles:]
    
    try:
        # Read current content
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply search/replace with retry logic
        result = apply_search_replace_block(content, edit_block, max_retries=2)
        
        if not result.success:
            error_msg = f"ERROR: Edit failed for article '{title}' - {result.message}"
            _log_tool_call("edit_article", {"title": title, "edit_block": edit_block}, error_msg)
            return Command(
                update={"linked_articles": linked_articles},
                resume=error_msg
            )
        
        # Write back the new content
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(result.new_content)
        
        success_msg = f"Successfully edited article '{title}' - {result.message}"
        _log_tool_call("edit_article", {"title": title, "edit_block": edit_block}, success_msg)
        return Command(
            update={"linked_articles": linked_articles},
            resume=success_msg
        )
        
    except Exception as e:
        error_msg = f"ERROR: Failed to edit article - {str(e)}"
        _log_tool_call("edit_article", {"title": title, "edit_block": edit_block}, error_msg)
        return Command(
            update={"linked_articles": linked_articles},
            resume=error_msg
        )

def _generate_image_dalle(art_prompt: str, size: str = None) -> str:
    """Generate image using DALLE-3."""
    import os
    api_key = os.getenv('OPENAI_API_KEY', 'NOT_SET')
    print(f"🔑 DALLE API key: {api_key[:8]}...{api_key[-4:] if len(api_key) >= 4 else 'SHORT'}")
    
    client = OpenAI()
    
    # Use provided size or fall back to config
    image_size = size or config["image"]["size"]
    print(f"🖼️ Generating {image_size} image")
    
    response = client.images.generate(
        model="dall-e-3",
        prompt=art_prompt,
        size=image_size,
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

def _parse_aspect_ratio_to_size(aspect_ratio: str) -> str:
    """Parse aspect ratio string and return DALL-E compatible size string.
    
    Args:
        aspect_ratio: String like "16:9", "1:1", "9:16"
        
    Returns:
        Size string like "1792x1024", "1024x1024", "1024x1792"
        The smaller dimension is scaled to 1024px.
    """
    try:
        # Parse ratio
        parts = aspect_ratio.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid format")
        
        width_ratio = float(parts[0])
        height_ratio = float(parts[1])
        
        # Calculate dimensions with smaller side = 1024
        if width_ratio <= height_ratio:
            # Width is smaller or equal, scale width to 1024
            width = 1024
            height = int((height_ratio / width_ratio) * 1024)
        else:
            # Height is smaller, scale height to 1024  
            height = 1024
            width = int((width_ratio / height_ratio) * 1024)
        
        # Return the calculated size
        return f"{width}x{height}"
                
    except (ValueError, ZeroDivisionError):
        # Default to 16:9 landscape if parsing fails
        return "1792x1024"

@mcp.tool()
def create_image(art_prompt: str, aspect_ratio: str = "16:9") -> str:
    """Generate artwork for wiki articles using AI image generation (DALLE, Replicate, etc).
    
    Use this tool to create visual representations of characters, locations, objects, or scenes
    from the story. Images are automatically saved to the story's images directory.
    
    Args:
        art_prompt: Detailed artistic description of what to generate. Be specific about:
                   - Subject matter (character, location, object, scene)
                   - Visual style (fantasy art, portrait, landscape, etc.)
                   - Important details (clothing, architecture, mood, lighting)
                   Example: "A tall wizard with silver beard in flowing blue robes, fantasy art style"
                   
        aspect_ratio: Image aspect ratio as string (default "16:9"). Examples:
                     - "16:9" -> 1792x1024 (landscape)
                     - "9:16" -> 1024x1792 (portrait)  
                     - "1:1" -> 1024x1024 (square)
                     - "3:4" -> 1024x1365 (portrait)
                     - "4:3" -> 1365x1024 (landscape)
                     The smaller dimension is scaled to 1024px.
                   
                   FILENAME GENERATION:
                   - Filename created from first 50 characters of prompt
                   - Special characters removed, spaces become hyphens
                   - Duplicate filenames get "-2", "-3", etc. suffixes
                   - Always saved as .png format
        
    Returns:
        Success message with generated filename and save location, or ERROR message if:
        - Image generation API fails
        - Unsupported generator configured
        - Network/download issues occur
        - File write operation fails
        
        Note: Generator used depends on config.toml [image] settings.
    """
    # Parse aspect ratio to get image size
    image_size = _parse_aspect_ratio_to_size(aspect_ratio)
    
    # Get configured image generator
    generator: str = config["image"]["generator"].lower()
    
    # Generate image based on configured generator
    if generator == "dalle":
        image_url = _generate_image_dalle(art_prompt, image_size)
    elif generator == "replicate":
        image_url = _generate_image_replicate(art_prompt)
    elif generator == "midjourney":
        image_url = _generate_image_midjourney(art_prompt)
    else:
        error_msg = f"ERROR: Unsupported image generator: {generator}. Supported: dalle, replicate, midjourney"
        _log_tool_call("create_image", {"art_prompt": art_prompt, "aspect_ratio": aspect_ratio}, error_msg)
        return error_msg
    
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
    
    success_msg = f"Successfully created image using {generator}: {filename}\nAspect ratio: {aspect_ratio} ({image_size})\nPrompt: {art_prompt}\nSaved to: {image_path}"
    _log_tool_call("create_image", {"art_prompt": art_prompt, "aspect_ratio": aspect_ratio}, success_msg)
    return success_msg

def _log_tool_call(tool_name: str, args: dict, result: str) -> None:
    """Log tool usage for debugging and monitoring."""
    import sys
    
    # Truncate long strings for readability
    def truncate_string(s: str, max_length: int = 150) -> str:
        if len(s) <= max_length:
            return s
        return s[:max_length] + "..."
    
    log_message = f"""
{"=" * 60}
🔧 TOOL CALLED: {tool_name.upper()}
{"=" * 60}"""
    
    if args:
        log_message += "\n📋 ARGUMENTS:"
        for key, value in args.items():
            if isinstance(value, str):
                log_message += f"\n  • {key}: {truncate_string(value)}"
            else:
                log_message += f"\n  • {key}: {value}"
    else:
        log_message += "\n📋 ARGUMENTS: None"
    
    log_message += f"\n✅ RESULT: {truncate_string(result)}"
    log_message += f"\n{'=' * 60}\n"
    
    # Print to both stdout and stderr to ensure visibility
    print(log_message, flush=True)
    print(log_message, file=sys.stderr, flush=True)

@mcp.tool()
def exit_when_complete(
    state: Annotated[WikiAgentState, InjectedState] = None
) -> str:
    """Call this tool when you have completely finished processing the entire story and created all possible wiki articles.
    
    This signals that you are done with the wiki creation process. Only call this when:
    - You have read through the entire story to the end
    - You see the end of story marker in the text
    - You have created comprehensive wiki articles for all notable elements
    - You believe the wiki documentation is complete and thorough
    
    Args:
        None
        
    Returns:
        Confirmation message that the process is complete.
    """
    _log_tool_call("exit_when_complete", {}, "Wiki creation process marked as complete!")
    
    # Get story info from state
    story_info = state.get("story_info", {}) if state else {}
    
    if story_info:
        # Check if story is actually complete
        is_complete = story_info.get("complete", False)
        current_pos = story_info.get("position", 0)
        total_words = story_info.get("total_words", 0)
        
        if is_complete:
            return "✅ Wiki creation process complete! You have successfully processed the entire story and documented all notable elements."
        else:
            progress = (current_pos / total_words) * 100 if total_words else 0
            return f"⚠️ Note: You're exiting at {progress:.1f}% story completion (word {current_pos} of {total_words}). The story may not be fully processed."
    else:
        return "✅ Wiki creation process complete! No story information available to check completion status."

if __name__ == "__main__":
    # Log server start
    import sys
    print("🚀 MCP Server Starting - Tool logging enabled", file=sys.stderr, flush=True)
    
    # Run the MCP server with suppressed banner
    mcp.run(transport="stdio", show_banner=False)