#!/usr/bin/env python3
"""
MCP Server for Gemini Picture Book Generator

This MCP server provides AI-powered story generation capabilities using Google's Gemini API.
It can create unlimited scenes, generate images, and display stories as artifacts.

Features:
- Generate stories with unlimited scenes
- Create AI-generated images for each scene
- Export to HTML and PDF formats
- Real-time progress tracking
- Gallery management
- Story customization (characters, settings, art styles)

Author: Assistant
Date: 2025-06-07
Version: 2.1.0 - MCP Server Edition
"""

import asyncio
import atexit
import json
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any  # Dict, List, Set removed

# Third-party imports
import aiofiles
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.prompts import base

# Import our existing story generation functions
from .enhanced_story_generator import (
    create_html_display,
    create_pdf_from_html,
    generate_custom_story_with_images,
    setup_client,
    test_api_connection,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("gemini_picturebook_mcp.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# Global tracking for cleanup
running_processes: dict[str, Any] = {}
background_tasks: set[asyncio.Task] = set()
generation_status: dict[str, dict[str, Any]] = {}


def cleanup_processes():

    # Cancel background tasks
    for task in background_tasks:
        if not task.done():
            task.cancel()

    background_tasks.clear()
    running_processes.clear()
    generation_status.clear()
    logger.info("Cleanup completed")


def signal_handler(signum, frame):
    """Handle termination signals."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    cleanup_processes()
    sys.exit(0)


def track_background_task(task: asyncio.Task):
    """Track background tasks for proper cleanup."""
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


# Register signal handlers and cleanup
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
atexit.register(cleanup_processes)


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Manage application lifecycle with cleanup."""
    logger.info("Starting Gemini Picture Book Generator MCP Server...")

    # Test API connection on startup
    try:
        if test_api_connection():
            logger.info("✅ Gemini API connection verified")
        else:
            logger.warning("⚠️ Could not verify Gemini API connection")
    except Exception as e:
        logger.error(f"❌ API connection test failed: {e}")

    try:
        yield {"initialized_at": datetime.now().isoformat()}
    finally:
        logger.info("Shutting down MCP server...")
        cleanup_processes()


# Initialize MCP server with lifespan management
mcp = FastMCP(
    "Gemini Picture Book Generator",
    lifespan=app_lifespan,
    dependencies=[
        "google-genai>=0.4.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "mcp>=1.0.0",
        "aiofiles>=24.1.0",
    ],
)


# --- Helper functions for generate_story ---

async def _prepare_story_environment(
    story_prompt: str, num_scenes: int, ctx: Context | None
) -> tuple[int, str, Path]:
    """Validate inputs and set up story directory."""
    if not story_prompt.strip():
        raise ValueError("Story prompt is required")
    # Ensure num_scenes is at least 1, matching original behavior
    validated_num_scenes = max(1, num_scenes)

    story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    project_dir = Path(__file__).parent.parent
    output_dir = project_dir / "generated_stories" / story_id
    output_dir.mkdir(parents=True, exist_ok=True)

    if ctx:
        await ctx.info(f"📁 Created output directory: {output_dir}")
    return validated_num_scenes, story_id, output_dir

def _build_enhanced_story_prompt(
    story_prompt: str, character_name: str, setting: str, style: str
) -> str:
    """Build the enhanced story prompt with customizations."""
    enhanced_prompt = story_prompt
    if character_name:
        enhanced_prompt = f"A story about {character_name}: {story_prompt}"
    if setting:
        enhanced_prompt += f" The story takes place in {setting}."
    enhanced_prompt += f" Create this in {style} art style."
    return enhanced_prompt

async def _run_core_story_generation(
    client: Any, # Replace Any with actual client type if known
    enhanced_prompt: str,
    num_scenes: int,
    output_dir: Path,
    story_id: str,
    ctx: Context | None,
) -> dict:
    """Generate core story content using the client and update progress."""
    # Update generation_status to indicate core generation has started
    generation_status[story_id].update({
        "progress": 10,  # Arbitrary progress % for starting core generation
        "message": "Generating story content and images...",
    })

    story_data = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: generate_custom_story_with_images(
            client, enhanced_prompt, num_scenes, output_dir
        ),
    )

    if not story_data:
        raise RuntimeError("Story generation failed - check API quota and key")

    if ctx:
        generated_image_scenes = len([s for s in story_data.get('scenes', []) if s.get('type') == 'image'])
        await ctx.info(f"✅ Generated {generated_image_scenes} scenes")

    # Update generation_status after core generation is complete
    generation_status[story_id].update({
        "progress": 80,  # Arbitrary progress % after core generation
        "message": "Core story content generated.",
    })
    return story_data

async def _finalize_and_export_story(
    story_data: dict,
    story_id: str,
    character_name: str,
    setting: str,
    style: str,
    output_dir: Path,
    ctx: Context | None,
) -> dict:
    """Finalize story data, add metadata, create exports, and update progress."""
    if ctx:
        await ctx.info("📄 Creating HTML and PDF exports...")

    story_data.update({
        "id": story_id,
        "character_name": character_name,
        "setting": setting,
        "style": style,
        "output_dir": str(output_dir),
        "mcp_generated": True,
    })

    html_path = create_html_display(story_data, output_dir)
    story_data["html_path"] = html_path

    pdf_path = create_pdf_from_html(html_path, output_dir)
    if pdf_path:
        story_data["pdf_path"] = pdf_path

    metadata_path = output_dir / "story_metadata.json"
    async with aiofiles.open(metadata_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(story_data, indent=2, ensure_ascii=False))

    # Update generation_status after exports are done
    generation_status[story_id].update({
        "progress": 95,  # Arbitrary progress % after exports
        "message": "Story exports created.",
    })
    return story_data

# --- End of helper functions ---


@mcp.tool()
async def generate_story(
    story_prompt: str,
    num_scenes: int = 6,
    character_name: str = "",
    setting: str = "",
    style: str = "cartoon",
    ctx: Context | None = None,
) -> str:
    """
    Generate an AI-powered picture book story with unlimited scenes.

    Creates a complete story with AI-generated images, text content, and exports
    it to both HTML and PDF formats. No artificial scene limits!

    Args:
        story_prompt: The main story idea (required)
        num_scenes: Number of scenes to generate (1-9999+, your choice!)
        character_name: Optional main character name
        setting: Optional story setting/location
        style: Art style (cartoon, anime, realistic, watercolor, digital art, oil painting, sketch, fantasy art)

    Returns:
        JSON string with story data and file paths
    """
    story_id_for_error_handling: str | None = None
    try:
        if ctx:
            await ctx.info(f"🎨 Starting story generation: '{story_prompt}'")
            await ctx.info(f"📊 Scenes: {num_scenes}, Style: {style}")

        # Step 1: Validate inputs and prepare environment
        # num_scenes here will be the validated number of scenes
        num_scenes, story_id, output_dir = await _prepare_story_environment(
            story_prompt, num_scenes, ctx
        )
        story_id_for_error_handling = story_id

        # Step 2: Initialize generation status
        generation_status[story_id] = {
            "status": "initializing", "progress": 0,
            "message": "Setting up story generation...",
            "story_prompt": story_prompt, "num_scenes": num_scenes,
            "start_time": datetime.now().isoformat(),
        }

        # Step 3: Setup client
        if ctx:
            await ctx.info("🔌 Connecting to Gemini API...")
        client = setup_client()
        if not client:
            raise RuntimeError("Failed to initialize Gemini API client")

        # Step 4: Build enhanced prompt
        enhanced_prompt = _build_enhanced_story_prompt(
            story_prompt, character_name, setting, style
        )

        if ctx:
            await ctx.info(f"⏱️ Estimated time: ~{num_scenes * 6 / 60:.1f} minutes (rate limiting)")
            await ctx.report_progress(1, num_scenes + 2)  # Progress: Setup complete

        # Step 5: Generate story content (core logic)
        story_data = await _run_core_story_generation(
            client, enhanced_prompt, num_scenes, output_dir, story_id, ctx
        )

        if ctx:
            # Progress: Core generation complete, before exports
            await ctx.report_progress(num_scenes + 1, num_scenes + 2)

        # Step 6: Finalize story data and create exports
        story_data = await _finalize_and_export_story(
            story_data, story_id, character_name, setting, style, output_dir, ctx
        )

        # Step 7: Mark generation as complete
        generation_status[story_id].update({
            "status": "complete", "progress": 100,
            "data": story_data, "end_time": datetime.now().isoformat(),
        })

        if ctx:
            await ctx.info(f"🎉 Story generation complete! Saved to: {output_dir}")
            await ctx.report_progress(num_scenes + 2, num_scenes + 2) # Progress: All done

        logger.info(f"Successfully generated story {story_id} with {num_scenes} scenes")

        return json.dumps({
            "success": True, "story_id": story_id, "story_data": story_data,
            "output_directory": str(output_dir),
            "html_path": story_data.get("html_path"),
            "pdf_path": story_data.get("pdf_path"),
            "scenes_generated": len([s for s in story_data.get("scenes", []) if s.get("type") == "image"]),
        }, indent=2)

    except Exception as e:
        error_msg = f"Story generation failed: {e!s}"
        logger.error(error_msg, exc_info=True)

        if story_id_for_error_handling and story_id_for_error_handling in generation_status:
            generation_status[story_id_for_error_handling].update({
                "status": "error", "error": error_msg,
                "end_time": datetime.now().isoformat(),
            })
        # If story_id was never generated (e.g., error in _prepare_story_environment before story_id assignment)
        # story_id_for_error_handling would be None.
        return json.dumps({
            "success": False, "error": error_msg,
            "story_id": story_id_for_error_handling,
        }, indent=2)


@mcp.tool()
async def list_generated_stories(limit: int = 20) -> str:
    """
    List all generated stories in the gallery.

    Args:
        limit: Maximum number of stories to return (default 20)

    Returns:
        JSON string with list of stories and their metadata
    """
    try:
        project_dir = Path(__file__).parent.parent
        stories_dir = project_dir / "generated_stories"

        if not stories_dir.exists():
            return json.dumps({
                "success": True,
                "stories": [],
                "total_count": 0,
                "message": "No stories directory found",
            })

        stories = []
        story_dirs = sorted(
            stories_dir.glob("story_*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:limit]

        for story_dir in story_dirs:
            metadata_file = story_dir / "story_metadata.json"
            if metadata_file.exists():
                try:
                    async with aiofiles.open(metadata_file, encoding="utf-8") as f:
                        content = await f.read()
                        metadata = json.loads(content)

                    # Find files
                    html_files = list(story_dir.glob("*.html"))
                    pdf_files = list(story_dir.glob("*.pdf"))
                    image_files = list(story_dir.glob("scene_*.png"))

                    # Calculate file sizes
                    total_size = sum(f.stat().st_size for f in story_dir.iterdir()) / 1024 / 1024  # MB

                    story_info = {
                        "id": story_dir.name,
                        "folder": story_dir.name,
                        "original_prompt": metadata.get("original_prompt", "Unknown"),
                        "num_scenes": metadata.get("num_scenes", 0),
                        "character_name": metadata.get("character_name", ""),
                        "setting": metadata.get("setting", ""),
                        "style": metadata.get("style", "cartoon"),
                        "generated_at": metadata.get("generated_at", ""),
                        "image_count": len(image_files),
                        "file_size_mb": round(total_size, 2),
                        "has_html": len(html_files) > 0,
                        "has_pdf": len(pdf_files) > 0,
                        "html_file": html_files[0].name if html_files else None,
                        "pdf_file": pdf_files[0].name if pdf_files else None,
                        "output_directory": str(story_dir),
                    }

                    stories.append(story_info)

                except Exception as e:
                    logger.warning(f"Could not process story metadata: {e}")
                    continue

        total_scenes = sum(s.get("num_scenes", 0) for s in stories)
        total_size = sum(s.get("file_size_mb", 0) for s in stories)

        return json.dumps({
            "success": True,
            "stories": stories,
            "total_count": len(stories),
            "total_scenes": total_scenes,
            "total_size_mb": round(total_size, 2),
            "directory": str(stories_dir),
        }, indent=2)

    except Exception as e:
        error_msg = f"Failed to list stories: {e!s}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({"success": False, "error": error_msg})


@mcp.tool()
async def get_story_details(story_id: str) -> str:
    """
    Get detailed information about a specific story.

    Args:
        story_id: The ID of the story to retrieve

    Returns:
        JSON string with complete story details and metadata
    """
    try:
        project_dir = Path(__file__).parent.parent
        story_dir = project_dir / "generated_stories" / story_id

        if not story_dir.exists():
            return json.dumps({
                "success": False,
                "error": f"Story {story_id} not found",
            })

        metadata_file = story_dir / "story_metadata.json"
        if not metadata_file.exists():
            return json.dumps({
                "success": False,
                "error": f"Story metadata not found for {story_id}",
            })

        async with aiofiles.open(metadata_file, encoding="utf-8") as f:
            content = await f.read()
            story_data = json.loads(content)

        # Add file information
        html_files = list(story_dir.glob("*.html"))
        pdf_files = list(story_dir.glob("*.pdf"))
        image_files = list(story_dir.glob("scene_*.png"))

        story_data.update({
            "output_directory": str(story_dir),
            "html_files": [f.name for f in html_files],
            "pdf_files": [f.name for f in pdf_files],
            "image_files": [f.name for f in image_files],
            "total_files": len(list(story_dir.iterdir())),
            "file_size_mb": round(
                sum(f.stat().st_size for f in story_dir.iterdir()) / 1024 / 1024, 2
            ),
        })

        return json.dumps({
            "success": True,
            "story_data": story_data,
        }, indent=2)

    except Exception as e:
        error_msg = f"Failed to get story details: {e!s}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({"success": False, "error": error_msg})


# --- Helper functions for display_story_as_artifact ---

def _generate_artifact_html_head(story_data: dict) -> str:
    """Generates the HTML head and styles for the artifact."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{story_data.get('original_prompt', 'AI Story')}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            line-height: 1.6;
        }}
        .story-header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .story-title {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .story-meta {{
            font-size: 1.1rem;
            opacity: 0.9;
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }}
        .story-meta div {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .scene {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            margin: 25px 0;
            padding: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
            backdrop-filter: blur(10px);
        }}
        .scene-number {{
            color: #667eea;
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .scene-image {{
            width: 100%;
            max-width: 600px;
            height: auto;
            border-radius: 12px;
            border: 3px solid #ddd;
            margin: 20px auto;
            display: block;
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
            transition: transform 0.3s ease;
        }}
        .scene-image:hover {{
            transform: scale(1.02);
        }}
        .scene-text {{
            font-size: 1.1rem;
            line-height: 1.8;
            color: #444;
            text-align: justify;
            margin: 15px 0;
            text-indent: 1.5em;
        }}
        .story-info {{
            background: rgba(103, 126, 234, 0.1);
            border: 2px solid #667eea;
            border-radius: 12px;
            padding: 20px;
            margin: 25px 0;
            color: #333;
        }}
        .story-info h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}
        .story-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat {{
            text-align: center;
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 0.9rem;
            color: #666;
            margin-top: 5px;
        }}
        .generated-info {{
            text-align: center;
            font-size: 0.9rem;
            color: #888;
            margin-top: 40px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 10px;
        }}
        @media (max-width: 768px) {{
            .story-meta {{
                flex-direction: column;
                gap: 15px;
            }}
            .story-title {{
                font-size: 2rem;
            }}
            .scene {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
"""

def _generate_artifact_story_header(story_data: dict) -> str:
    """Generates the story header section for the artifact."""
    return f"""
    <div class="story-header">
        <div class="story-title">📚 {story_data.get('original_prompt', 'AI Story')}</div>
        <div class="story-meta">
            <div>👤 {story_data.get('character_name') or 'Auto-chosen'}</div>
            <div>🎨 {story_data.get('style', 'cartoon').title()} Style</div>
            <div>📍 {story_data.get('setting') or 'Auto-chosen'}</div>
            <div>🎬 {story_data.get('num_scenes', 0)} Scenes</div>
        </div>
    </div>
"""

def _generate_artifact_story_info_section(story_data: dict) -> str:
    """Generates the story information section for the artifact."""
    return f"""
    <div class="story-info">
        <h3>📖 Story Information</h3>
        <div class="story-stats">
            <div class="stat">
                <div class="stat-value">{story_data.get('num_scenes', 0)}</div>
                <div class="stat-label">Scenes</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len([s for s in story_data.get('scenes', []) if s.get('type') == 'image'])}</div>
                <div class="stat-label">Images</div>
            </div>
            <div class="stat">
                <div class="stat-value">{story_data.get('file_size_mb', 0)} MB</div>
                <div class="stat-label">File Size</div>
            </div>
            <div class="stat">
                <div class="stat-value">{story_data.get('total_parts', 0)}</div>
                <div class="stat-label">AI Parts</div>
            </div>
        </div>
    </div>
"""

def _group_scenes(story_data: dict) -> tuple[dict[int, list[str]], dict[int, Any]]:
    """Groups scenes by type (text/image) and scene number."""
    text_scenes: dict[int, list[str]] = {}
    image_scenes: dict[int, Any] = {}

    for scene in story_data.get("scenes", []):
        scene_num = scene.get("scene_number")
        # Ensure scene_num is an integer before using it as a key
        if not isinstance(scene_num, int):
            logger.warning(f"Skipping scene with non-integer scene_number: {scene_num}")
            continue

        if scene.get("type") == "text":
            if scene_num not in text_scenes:
                text_scenes[scene_num] = []
            text_scenes[scene_num].append(scene.get("content", ""))
        elif scene.get("type") == "image":
            image_scenes[scene_num] = scene
    return text_scenes, image_scenes

def _generate_html_for_image(scene_num: int, image_scene_data: Any, story_dir: Path) -> str:
    """Generates HTML for a single image scene, embedding the image."""
    image_html = ""
    image_filename = image_scene_data.get("filename")
    if not image_filename:
        logger.warning(f"Image scene {scene_num} has no filename.")
        return '        <div style="color: #999; text-align: center; padding: 20px;">Missing image filename</div>\n'

    image_path = story_dir / image_filename
    if image_path.exists():
        try:
            import base64
            with open(image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
            image_html = f'        <img src="data:image/png;base64,{img_data}" alt="Scene {scene_num}" class="scene-image">\n'
        except Exception as e:
            logger.error(f"Error embedding image {image_path} for scene {scene_num}: {e}")
            image_html = f'        <div style="color: #999; text-align: center; padding: 20px;">Error loading image for Scene {scene_num} ({image_filename})</div>\n'
    else:
        logger.warning(f"Image file not found for scene {scene_num}: {image_path}")
        image_html = f'        <div style="color: #999; text-align: center; padding: 20px;">Image not found for Scene {scene_num} ({image_filename})</div>\n'
    return image_html

def _generate_html_for_text(text_contents: list[str]) -> str:
    """Generates HTML for text content of a scene, handling paragraphs."""
    text_html_parts = []
    for text_content in text_contents:
        if text_content and text_content.strip():
            paragraphs = text_content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    text_html_parts.append(f'        <div class="scene-text">{paragraph.strip()}</div>\n')
    return "".join(text_html_parts)

def _generate_artifact_scenes_html(story_data: dict, story_dir: Path) -> str:
    """Generates HTML for all scenes, including images and text."""
    scenes_html_parts = []
    text_scenes, image_scenes = _group_scenes(story_data)

    all_scene_numbers = set(text_scenes.keys()) | set(image_scenes.keys())
    # Ensure we only process valid integer scene numbers, sorted
    actual_scene_numbers = sorted([sn for sn in all_scene_numbers if isinstance(sn, int)])

    for scene_num in actual_scene_numbers:
        scenes_html_parts.append('    <div class="scene">\n')
        scenes_html_parts.append(f'        <div class="scene-number">🎬 Scene {scene_num}</div>\n')

        if scene_num in image_scenes:
            scenes_html_parts.append(
                _generate_html_for_image(scene_num, image_scenes[scene_num], story_dir)
            )

        if scene_num in text_scenes:
            scenes_html_parts.append(
                _generate_html_for_text(text_scenes[scene_num])
            )

        scenes_html_parts.append('    </div>\n\n')

    return "".join(scenes_html_parts)

def _generate_artifact_footer(story_id: str, story_data: dict) -> str:
    """Generates the footer section for the artifact."""
    return f"""
    <div class="generated-info">
        <p>✨ Generated with Google Gemini AI via MCP Server ✨</p>
        <p>Created: {story_data.get('generated_at', 'Unknown date')}</p>
        <p>Model: {story_data.get('model', 'gemini-2.0-flash-preview-image-generation')}</p>
        <p>Story ID: {story_id}</p>
    </div>
</body>
</html>
"""

# --- End of helper functions for display_story_as_artifact ---

@mcp.tool()
async def display_story_as_artifact(story_id: str, ctx: Context | None = None) -> str:
    """
    Create an HTML artifact to display a generated story with images.

    Args:
        story_id: The ID of the story to display

    Returns:
        HTML content suitable for display as an artifact
    """
    try:
        story_details_json = await get_story_details(story_id)
        story_info = json.loads(story_details_json)

        if not story_info.get("success"):
            return f"<div class='error'>Error: {story_info.get('error', 'Unknown error')}</div>"

        story_data = story_info["story_data"]
        story_dir = Path(story_data["output_directory"])

        if ctx:
            await ctx.info(f"📖 Displaying story: {story_data.get('original_prompt', 'Unknown')}")

        html_content = _generate_artifact_html_head(story_data)
        html_content += _generate_artifact_story_header(story_data)
        html_content += _generate_artifact_story_info_section(story_data)
        html_content += _generate_artifact_scenes_html(story_data, story_dir)
        html_content += _generate_artifact_footer(story_id, story_data)

        logger.info(f"Generated artifact for story {story_id}")
        return html_content

    except Exception as e:
        error_msg = f"Failed to create story artifact: {e!s}"
        logger.error(error_msg, exc_info=True)
        return f"<div class='error' style='color: red; padding: 20px; text-align: center;'>Error: {error_msg}</div>"


@mcp.tool()
async def get_generation_status(story_id: str) -> str:
    """
    Check the status of an ongoing story generation.

    Args:
        story_id: The ID of the story being generated

    Returns:
        JSON string with current generation status
    """
    if story_id in generation_status:
        return json.dumps(generation_status[story_id], indent=2)
    else:
        return json.dumps({
            "error": f"Generation {story_id} not found",
            "available_ids": list(generation_status.keys()),
        })


@mcp.tool()
async def test_gemini_connection() -> str:
    """
    Test the connection to Google's Gemini API.

    Returns:
        JSON string with connection test results
    """
    try:
        logger.info("Testing Gemini API connection...")

        # Check if API key is configured
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_api_key_here":
            return json.dumps({
                "success": False,
                "error": "Google API key not configured properly",
                "help": "Set GOOGLE_API_KEY environment variable or update .env file",
                "get_key_url": "https://aistudio.google.com/app/apikey",
            })

        # Test connection
        success = test_api_connection()

        if success:
            return json.dumps({
                "success": True,
                "message": "✅ Gemini API connection successful",
                "api_key_configured": True,
                "timestamp": datetime.now().isoformat(),
            })
        else:
            return json.dumps({
                "success": False,
                "error": "Failed to connect to Gemini API",
                "api_key_configured": True,
                "help": "Check API key validity and quota limits",
            })

    except Exception as e:
        error_msg = f"Connection test failed: {e!s}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "success": False,
            "error": error_msg,
        })


# Resource for providing story generation guidance
@mcp.resource("guidance://story-generation")
def get_story_guidance() -> str:
    """Comprehensive guide for using the Gemini Picture Book Generator."""
    return """# Gemini Picture Book Generator - User Guide

## 🎨 Overview
This MCP server provides AI-powered story generation using Google's Gemini API. Create unlimited picture books with custom scenes, characters, and art styles.

## 🚀 Quick Start

### 1. Generate a Story
```
generate_story(
    story_prompt="A robot learning to paint masterpieces",
    num_scenes=6,
    character_name="Artie",
    setting="art studio",
    style="cartoon"
)
```

### 2. View Generated Stories
```
list_generated_stories(limit=10)
```

### 3. Display as Artifact
```
display_story_as_artifact(story_id="story_20250607_143022_123456")
```

## 🎭 Available Art Styles
- **cartoon**: Fun, colorful, kid-friendly
- **anime**: Japanese animation style
- **realistic**: Photographic quality
- **watercolor**: Soft, artistic painting
- **digital art**: Modern digital illustration
- **oil painting**: Classic painted style
- **sketch**: Hand-drawn pencil style
- **fantasy art**: Epic, magical themes

## 📊 Features

### Unlimited Scenes
- No artificial limits on story length
- Generate 1-9999+ scenes (your choice!)
- Rate limited by API: ~6 seconds per scene

### Customization Options
- Character names and settings
- Multiple art styles
- Custom story prompts
- Real-time progress tracking

### Export Formats
- HTML with embedded images
- PDF for easy sharing
- JSON metadata for programmatic access

## ⏱️ Generation Times
- **3 scenes**: ~18 seconds
- **6 scenes**: ~36 seconds
- **12 scenes**: ~1.2 minutes
- **25 scenes**: ~2.5 minutes
- **50 scenes**: ~5 minutes
- **100 scenes**: ~10 minutes

## 🔧 API Requirements
- Google API key required
- Free tier: 1,500 requests/day
- Rate limit: 10 requests/minute
- Model: gemini-2.0-flash-preview-image-generation

## 📁 File Structure
```
generated_stories/
├── story_20250607_143022_123456/
│   ├── scene_01.png
│   ├── scene_02.png
│   ├── story.html
│   ├── story.pdf
│   └── story_metadata.json
```

## 🎯 Best Practices

### Story Prompts
- Be descriptive and specific
- Include emotions and actions
- Mention target audience if relevant
- Example: "A shy dragon who discovers friendship through helping others"

### Scene Counts
- **3-6 scenes**: Quick stories, testing
- **8-15 scenes**: Classic picture books
- **20-30 scenes**: Chapter books
- **50+ scenes**: Novels, epics

### Character Names
- Simple, memorable names work best
- Consider the target audience
- Examples: Luna, Max, Zara, Captain Stardust

### Settings
- Vivid, imaginative locations
- Examples: "enchanted forest", "space station", "underwater city"

## 🛟 Troubleshooting

### Common Issues
1. **API Connection Failed**
   - Check GOOGLE_API_KEY environment variable
   - Verify key at https://aistudio.google.com/app/apikey

2. **Generation Slow/Stalled**
   - Normal due to 6-second rate limiting
   - Large stories take time (50 scenes = ~5 minutes)

3. **Out of Quota**
   - Free tier: 1,500 requests/day
   - Wait 24 hours or upgrade plan

4. **Images Not Generating**
   - Check API quota
   - Verify image generation model access

### Getting Help
Use `test_gemini_connection()` to diagnose API issues.

## 🎉 Example Workflows

### Quick Test Story
```python
# Generate a simple 3-scene story
result = await generate_story(
    story_prompt="A cat who becomes a superhero",
    num_scenes=3,
    style="cartoon"
)

# Display it immediately
story_data = json.loads(result)
if story_data["success"]:
    await display_story_as_artifact(story_data["story_id"])
```

### Epic Adventure
```python
# Create a long-form story
result = await generate_story(
    story_prompt="The chronicles of a young wizard saving multiple realms",
    num_scenes=50,
    character_name="Luna Stardust",
    setting="magical multiverse",
    style="fantasy art"
)
```

### Gallery Management
```python
# List all stories
stories = await list_generated_stories(limit=20)

# Get details for specific story
details = await get_story_details("story_20250607_143022_123456")

# Display any story as artifact
await display_story_as_artifact("story_20250607_143022_123456")
```

## 🌟 Pro Tips
1. **Start small**: Test with 3-6 scenes first
2. **Be patient**: Large stories take time due to rate limits
3. **Save story IDs**: Use them to redisplay stories later
4. **Use descriptive prompts**: Better prompts = better stories
5. **Experiment with styles**: Different styles suit different stories
6. **Plan for time**: 100-scene stories take ~10 minutes

## 📚 Story Examples

### Children's Bedtime Story
```
Prompt: "A sleepy bunny who helps other forest animals find their way home"
Scenes: 6
Character: "Rosie"
Setting: "peaceful meadow"
Style: "watercolor"
```

### Adventure Epic
```
Prompt: "A space explorer discovering ancient alien mysteries across the galaxy"
Scenes: 25
Character: "Captain Nova"
Setting: "distant star systems"
Style: "digital art"
```

### Educational Story
```
Prompt: "A young scientist learning about the water cycle through magical adventures"
Scenes: 12
Character: "Dr. Maya"
Setting: "nature laboratory"
Style: "realistic"
```

Ready to create amazing stories? Start with `generate_story()` and let your imagination run wild! 🚀✨
"""


# Prompts for guided story creation
@mcp.prompt()
def create_story_prompt(
    theme: str = "adventure",
    audience: str = "children",
    length: str = "short",
) -> str:
    """Generate a story prompt based on theme, audience, and desired length."""

    themes = {
        "adventure": "brave exploration and exciting journeys",
        "friendship": "the power of friendship and helping others",
        "learning": "discovery, education, and growing knowledge",
        "fantasy": "magical realms, mythical creatures, and wonder",
        "animals": "animal characters with human-like qualities",
        "science": "scientific concepts made fun and accessible",
        "mystery": "puzzles, secrets, and detective work",
        "emotions": "understanding feelings and emotional growth",
    }

    lengths = {
        "short": (3, 6),
        "medium": (8, 15),
        "long": (20, 30),
        "epic": (50, 100),
    }

    theme_desc = themes.get(theme, "exciting adventures")
    min_scenes, max_scenes = lengths.get(length, (6, 12))

    return f"""Create a {audience}-friendly story about {theme_desc}.

Suggested prompt: "A story that teaches {audience} about {theme_desc} through engaging characters and situations."

Recommended settings:
- num_scenes: {min_scenes}-{max_scenes} (for {length} stories)
- style: Choose based on audience and theme
- character_name: Give your protagonist a memorable name
- setting: Create an immersive world for your story

Example usage:
```
generate_story(
    story_prompt="Your creative story idea here...",
    num_scenes={min_scenes},
    character_name="Hero Name",
    setting="Story World",
    style="cartoon"
)
```

Remember: Be descriptive, include emotions, and make it engaging for your target audience!"""


@mcp.prompt()
def story_troubleshooting() -> list[base.Message]: # Using list[base.Message] as it's more modern
    """Help troubleshoot common story generation issues."""

    return [
        # The stray parenthesis was removed here.
        # If a SystemMessage was intended, it should be added correctly.
        # For now, assuming it was an error.
        base.AssistantMessage(
            "I'd be happy to help! Let me guide you through common issues and solutions.\n\n"
            "First, let's test your API connection:"
        ),
        base.UserMessage(
            "Please run: test_gemini_connection()"
        ),
        base.AssistantMessage(
            "Based on the results, here are common issues and fixes:\n\n"
            "**API Connection Issues:**\n"
            "- Missing/invalid API key → Get key from https://aistudio.google.com/app/apikey\n"
            "- Set GOOGLE_API_KEY environment variable\n\n"
            "**Generation Problems:**\n"
            "- Slow generation → Normal! 6-second rate limiting per scene\n"
            "- Failed generation → Check API quota (1,500 requests/day free)\n"
            "- No images → Verify image generation model access\n\n"
            "**Large Stories:**\n"
            "- 50+ scenes take 5+ minutes (be patient!)\n"
            "- Start with 3-6 scenes for testing\n\n"
            "Try a simple test story first:\n"
            "```\n"
            "generate_story(\n"
            "    story_prompt='A friendly robot learning to dance',\n"
            "    num_scenes=3,\n"
            "    style='cartoon'\n"
            ")\n"
            "```"
        ),
    ]


def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("🚀 Starting Gemini Picture Book Generator MCP Server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        cleanup_processes()


if __name__ == "__main__":
    main()
