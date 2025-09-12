"""
Image generation tool for creating artwork using AI image generators.
"""
import os
import re
import toml
import requests
from pathlib import Path
from typing import Optional


def _map_orientation_to_size(orientation: str) -> str:
    """Map human-friendly orientation to DALL·E-compatible size.

    Supported orientations:
    - square -> 1024x1024
    - landscape -> 1792x1024
    - portrait -> 1024x1792

    Falls back to landscape if input is invalid.
    """
    key = (orientation or "").strip().lower()
    if key == "square":
        return "1024x1024"
    if key == "portrait":
        return "1024x1792"
    # Default and explicit landscape
    return "1792x1024"


def _generate_image_dalle(art_prompt: str, size: str = None) -> str:
    """Generate image using DALLE-3."""
    from openai import OpenAI
    
    # Load config for image settings
    config = toml.load("config.toml")
    
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


def _generate_slugified_filename(prompt: str) -> str:
    """Generate a slugified filename from the prompt."""
    filename_base = re.sub(r'[^\w\s-]', '', prompt.lower())
    filename_base = re.sub(r'[-\s]+', '-', filename_base).strip('-')
    return filename_base[:50]  # Limit length


def _find_existing_image(filename_base: str, images_dir: Path) -> Optional[Path]:
    """Check if an image with similar filename already exists."""
    # Check for exact match first
    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        image_path = images_dir / f"{filename_base}{ext}"
        if image_path.exists():
            return image_path
    
    # Check for numbered variants
    for counter in range(1, 10):  # Check first 10 variants
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            if counter == 1:
                image_path = images_dir / f"{filename_base}{ext}"
            else:
                image_path = images_dir / f"{filename_base}-{counter}{ext}"
            if image_path.exists():
                return image_path
    
    return None


def _find_unique_filename(filename_base: str, images_dir: Path, extension: str = '.png') -> Path:
    """Find a unique filename, adding counter suffix if needed."""
    counter = 1
    while True:
        if counter == 1:
            filename = f"{filename_base}{extension}"
        else:
            filename = f"{filename_base}-{counter}{extension}"
            
        image_path = images_dir / filename
        if not image_path.exists():
            return image_path
        counter += 1


def create_image(art_prompt: str, name: str, orientation: str = "landscape") -> str:
    """Generate artwork for wiki articles using AI image generation (DALLE, etc).
    
    Use this tool to create visual representations of characters, locations, objects, or scenes
    from stories. Images are automatically saved to the story's images directory.
    
    Parameters
    ----------
    art_prompt : str
        Detailed artistic description of what to generate. Be specific about:
        - Subject matter (character, location, object, scene)
        - Visual style (fantasy art, portrait, landscape, etc.)
        - Important details (clothing, architecture, mood, lighting)
        Example: "A tall wizard with silver beard in flowing blue robes, fantasy art style"
        
    name : str
        Name for the image file (without extension). Will be saved as <name>.png.
        Use descriptive names like "wizard-merlin", "london-cityscape", "haunted-mansion".
        Special characters will be cleaned and spaces converted to hyphens.
        
    orientation : str, default "landscape"
        One of: "square", "landscape", or "portrait".
        These map to the DALL·E-3 supported sizes:
        - square -> 1024x1024
        - landscape -> 1792x1024
        - portrait -> 1024x1792
        
    Returns
    -------
    str
        Success message with generated filename and save location, or ERROR message if:
        - Image generation API fails
        - Unsupported generator configured
        - Network/download issues occur
        - File write operation fails
    """
    # Load configuration
    try:
        config = toml.load("config.toml")
    except Exception as e:
        return f"ERROR: Could not load config.toml: {str(e)}"
    
    # Create filename from name parameter
    filename_base = _generate_slugified_filename(name)
    
    # Create images directory path
    story_name = config["story"]["current_story"]
    images_dir = Path(config["paths"]["content_dir"]) / story_name / config["paths"]["images_dir"]
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if image with this name already exists
    existing_image = _find_existing_image(filename_base, images_dir)
    if existing_image:
        return f"Image already exists: {existing_image.name}\nPath: {existing_image}\nName was: {name}\nUse a different name if you want to create a new image."
    
    # Map orientation to DALL·E size
    image_size = _map_orientation_to_size(orientation)
    
    # Get configured image generator
    generator = config["image"]["generator"].lower()
    
    # Generate image based on configured generator
    if generator == "dalle":
        try:
            # Try to import specific error for clearer handling
            try:
                from openai import BadRequestError as _OpenAIBadRequestError
            except Exception:
                _OpenAIBadRequestError = Exception  # Fallback

            image_url = _generate_image_dalle(art_prompt, image_size)
        except _OpenAIBadRequestError as e:
            guidance = (
                "DALL·E 3 may reject prompts involving: real people/public figures, sexual or erotic content, "
                "self-harm, hate/harassment, graphic violence or gore, illegal activities, political persuasion, "
                "copyrighted logos/brands, or personal data (PII/PHI). Rephrase to use fictional or generic subjects, "
                "avoid explicit/graphic details, omit names/trademarks, and keep content safe and non-violent."
            )
            return f"ERROR: DALLE request rejected: {str(e)}\nAdvice: {guidance}"
        except Exception as e:
            guidance = (
                "If this is a safety rejection, try: fictional/generic subjects, avoid explicit content, "
                "graphic violence, illegal activities, targeted hate, political persuasion, trademarks/brands, "
                "or personal data. Use safer, non-graphic rephrasing without names or logos."
            )
            return f"ERROR: DALLE request failed: {str(e)}\nAdvice: {guidance}"
    else:
        return f"ERROR: Unsupported image generator: {generator}. Currently only 'dalle' is supported."
    
    # Download the image
    try:
        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return (
            f"ERROR: Failed to download generated image: {str(e)}\n"
            f"URL: {image_url}\n"
            "Advice: Verify network connectivity and that the URL is accessible. "
            "If this persists, retry later or regenerate the image."
        )
    
    # Find unique filename and save image
    image_path = _find_unique_filename(filename_base, images_dir, '.png')
    
    try:
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
    except Exception as e:
        return f"ERROR: Failed to save image to disk: {str(e)}"
    
    return (
        f"Successfully created image using {generator}: {image_path.name}\n"
        f"Orientation: {orientation} ({image_size})\n"
        f"Prompt: {art_prompt}\n"
        f"Saved to: {image_path}"
    )


if __name__ == "__main__":
    # Test the image creation
    print("🧪 Testing create_image function...")
    result = create_image("A majestic castle on a hill at sunset, fantasy art style", "test-castle-sunset", "landscape")
    print(result)