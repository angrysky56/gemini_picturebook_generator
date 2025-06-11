#!/usr/bin/env python3
"""
Enhanced MCP Server for Gemini Picture Book Generator

This enhanced MCP server provides AI-powered story generation capabilities using Google's Gemini API
with automatic browser opening functionality.

Features:
- Generate stories with unlimited scenes
- Create AI-generated images for each scene
- Export to HTML and PDF formats
- AUTO-OPEN generated stories in browser
- Real-time progress tracking
- Gallery management
- Story customization (characters, settings, art styles)

Author: Assistant
Date: 2025-06-07
Version: 2.2.0 - Enhanced MCP Server Edition with Auto-Open
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
from typing import Any

import aiofiles
from mcp.server.fastmcp import Context, FastMCP

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

# Global tracking for cleanup
running_processes: dict[str, Any] = {}
background_tasks: set[asyncio.Task] = set()
generation_status: dict[str, dict[str, Any]] = {}


def cleanup_processes():
    """Clean up all running processes and background tasks."""
    logger.info("Cleaning up processes and tasks...")

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


async def open_file_in_browser(file_path: str) -> dict[str, Any]:
    """
    Open a file in the default browser using system commands.

    Args:
        file_path: Path to the file to open

    Returns:
        Dictionary with operation status
    """
    try:
        file_path = str(Path(file_path).resolve())

        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        # Platform-specific commands to open files in browser
        if sys.platform.startswith('linux'):
            # Linux - use xdg-open
            process = await asyncio.create_subprocess_exec(
                'xdg-open', file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Opened in browser: {file_path}",
                    "command": f"xdg-open {file_path}"
                }
            else:
                return {
                    "success": False,
                    "error": f"xdg-open failed: {stderr.decode()}"
                }

        elif sys.platform.startswith('darwin'):
            # macOS - use open
            process = await asyncio.create_subprocess_exec(
                'open', file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Opened in browser: {file_path}",
                    "command": f"open {file_path}"
                }
            else:
                return {
                    "success": False,
                    "error": f"open failed: {stderr.decode()}"
                }

        elif sys.platform.startswith('win'):
            # Windows - use start
            process = await asyncio.create_subprocess_exec(
                'cmd', '/c', 'start', file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Opened in browser: {file_path}",
                    "command": f"start {file_path}"
                }
            else:
                return {
                    "success": False,
                    "error": f"start failed: {stderr.decode()}"
                }
        else:
            return {
                "success": False,
                "error": f"Unsupported platform: {sys.platform}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to open file: {e!s}"
        }


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Manage application lifecycle with cleanup."""
    logger.info("Starting Enhanced Gemini Picture Book Generator MCP Server...")

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
    "Enhanced Gemini Picture Book Generator",
    lifespan=app_lifespan,
    dependencies=[
        "google-genai>=0.4.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "mcp>=1.0.0",
        "aiofiles>=24.1.0",
    ],
)


@mcp.tool()
async def generate_story(
    story_prompt: str,
    num_scenes: int = 6,
    character_name: str = "",
    setting: str = "",
    style: str = "cartoon",
    auto_open: bool = True,
    ctx: Context | None = None,
) -> str:
    """
    Generate an AI-powered picture book story with unlimited scenes.

    Args:
        story_prompt: The main story idea (required)
        num_scenes: Number of scenes to generate (1-9999+, your choice!)
        character_name: Optional main character name
        setting: Optional story setting/location
        style: Art style (cartoon, anime, realistic, watercolor, digital art, oil painting, sketch, fantasy art)
        auto_open: Automatically open the generated story in browser (default: True)

    Returns:
        JSON string with story data and file paths
    """
    story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    try:
        await _story_generation_log_start(ctx, story_prompt, num_scenes, style, auto_open)
        _validate_story_inputs(story_prompt)
        num_scenes = max(num_scenes, 1)
        output_dir = _create_output_dir(story_id)
        await _story_generation_log_dir(ctx, output_dir)
        _track_generation_status(story_id, story_prompt, num_scenes)
        client = _setup_gemini_client(ctx)
        enhanced_prompt = _build_enhanced_prompt(story_prompt, character_name, setting, style)
        await _story_generation_log_estimate(ctx, num_scenes)
        await _story_generation_log_progress(ctx, 1, num_scenes + 3)
        story_data = await _run_story_generation(client, enhanced_prompt, num_scenes, output_dir)
        await _story_generation_log_generated(ctx, story_data, num_scenes)
        _add_story_metadata(story_data, story_id, character_name, setting, style, output_dir)
        html_path, pdf_path = await _export_story(ctx, story_data, output_dir)
        await _save_story_metadata(story_data, output_dir)
        await _story_generation_log_progress(ctx, num_scenes + 2, num_scenes + 3)
        browser_result = await _maybe_open_in_browser(ctx, auto_open, html_path)
        _update_generation_status_complete(story_id, story_data, browser_result)
        await _story_generation_log_complete(ctx, output_dir, num_scenes + 3)
        logger.info(f"Successfully generated story {story_id} with {num_scenes} scenes")
        return _story_success_json(story_id, story_data, output_dir, html_path, pdf_path, browser_result)
    except Exception as e:
        return await _handle_story_generation_error(e, story_id)

# --- Helper functions for generate_story ---

def _validate_story_inputs(story_prompt: str):
    if not story_prompt.strip():
        raise ValueError("Story prompt is required")

def _create_output_dir(story_id: str) -> Path:
    project_dir = Path(__file__).parent.parent
    output_dir = project_dir / "generated_stories" / story_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def _track_generation_status(story_id: str, story_prompt: str, num_scenes: int):
    generation_status[story_id] = {
        "status": "initializing",
        "progress": 0,
        "message": "Setting up story generation...",
        "story_prompt": story_prompt,
        "num_scenes": num_scenes,
        "start_time": datetime.now().isoformat(),
    }

def _setup_gemini_client(ctx):
    if ctx:
        task = asyncio.create_task(ctx.info("🔌 Connecting to Gemini API..."))
        track_background_task(task)
    client = setup_client()
    if not client:
        raise RuntimeError("Failed to initialize Gemini API client")
    return client

def _build_enhanced_prompt(story_prompt, character_name, setting, style):
    enhanced_prompt = story_prompt
    if character_name:
        enhanced_prompt = f"A story about {character_name}: {story_prompt}"
    if setting:
        enhanced_prompt += f" The story takes place in {setting}."
    enhanced_prompt += f" Create this in {style} art style."
    return enhanced_prompt

async def _run_story_generation(client, enhanced_prompt, num_scenes, output_dir):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: generate_custom_story_with_images(
            client, enhanced_prompt, num_scenes, output_dir
        ),
    )

def _add_story_metadata(story_data, story_id, character_name, setting, style, output_dir):
    story_data.update({
        "id": story_id,
        "character_name": character_name,
        "setting": setting,
        "style": style,
        "output_dir": str(output_dir),
        "mcp_generated": True,
    })

async def _export_story(ctx, story_data, output_dir):
    if ctx:
        await ctx.info("📄 Creating HTML and PDF exports...")
    html_path = create_html_display(story_data, output_dir)
    story_data["html_path"] = html_path
    pdf_path = create_pdf_from_html(html_path, output_dir)
    if pdf_path:
        story_data["pdf_path"] = pdf_path
    return html_path, pdf_path

async def _save_story_metadata(story_data, output_dir):
    metadata_path = output_dir / "story_metadata.json"
    async with aiofiles.open(metadata_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(story_data, indent=2, ensure_ascii=False))

async def _maybe_open_in_browser(ctx, auto_open, html_path):
    browser_result = {"success": False, "message": "Auto-open disabled"}
    if auto_open and html_path:
        if ctx:
            await ctx.info("🌐 Opening story in browser...")
        browser_result = await open_file_in_browser(html_path)
        if ctx:
            if browser_result["success"]:
                await ctx.info(f"🎉 Story opened in browser: {html_path}")
            else:
                await ctx.warning(f"⚠️ Could not auto-open browser: {browser_result.get('error', 'Unknown error')}")
    return browser_result

def _update_generation_status_complete(story_id, story_data, browser_result):
    generation_status[story_id].update({
        "status": "complete",
        "progress": 100,
        "data": story_data,
        "browser_opened": browser_result["success"],
        "end_time": datetime.now().isoformat(),
    })

def _story_success_json(story_id, story_data, output_dir, html_path, pdf_path, browser_result):
    return json.dumps({
        "success": True,
        "story_id": story_id,
        "story_data": story_data,
        "output_directory": str(output_dir),
        "html_path": html_path,
        "pdf_path": pdf_path,
        "scenes_generated": len([s for s in story_data["scenes"] if s["type"] == "image"]),
        "browser_opened": browser_result["success"],
        "browser_message": browser_result.get("message", ""),
    }, indent=2)

async def _handle_story_generation_error(e, story_id):
    error_msg = f"Story generation failed: {e!s}"
    logger.error(error_msg, exc_info=True)
    if story_id in generation_status:
        generation_status[story_id].update({
            "status": "error",
            "error": error_msg,
            "end_time": datetime.now().isoformat(),
        })
    return json.dumps({
        "success": False,
        "error": error_msg,
        "story_id": story_id if "story_id" in locals() else None,
    }, indent=2)

async def _story_generation_log_start(ctx, story_prompt, num_scenes, style, auto_open):
    if ctx:
        await ctx.info(f"🎨 Starting story generation: '{story_prompt}'")
        await ctx.info(f"📊 Scenes: {num_scenes}, Style: {style}, Auto-open: {auto_open}")

async def _story_generation_log_dir(ctx, output_dir):
    if ctx:
        await ctx.info(f"📁 Created output directory: {output_dir}")

async def _story_generation_log_estimate(ctx, num_scenes):
    if ctx:
        await ctx.info(f"⏱️ Estimated time: ~{num_scenes * 6 / 60:.1f} minutes (rate limiting)")

async def _story_generation_log_progress(ctx, current, total):
    if ctx:
        await ctx.report_progress(current, total)

async def _story_generation_log_generated(ctx, story_data, num_scenes):
    if ctx:
        await ctx.info(f"✅ Generated {len([s for s in story_data['scenes'] if s['type'] == 'image'])} scenes")
        await ctx.report_progress(num_scenes + 1, num_scenes + 3)

async def _story_generation_log_complete(ctx, output_dir, progress):
    if ctx:
        await ctx.info(f"🎉 Story generation complete! Saved to: {output_dir}")
        await ctx.report_progress(progress, progress)


@mcp.tool()
async def open_story_in_browser(story_id: str, ctx: Context | None = None) -> str:
    """
    Open a generated story in the default browser.

    Args:
        story_id: The ID of the story to open

    Returns:
        JSON string with operation status
    """
    try:
        if ctx:
            await ctx.info(f"🌐 Opening story {story_id} in browser...")

        # Get story details
        story_details = await get_story_details(story_id)
        story_info = json.loads(story_details)

        if not story_info.get("success"):
            return json.dumps({
                "success": False,
                "error": story_info.get("error", "Story not found")
            })

        story_data = story_info["story_data"]

        # Find HTML file
        html_files = story_data.get("html_files", [])
        if not html_files:
            return json.dumps({
                "success": False,
                "error": "No HTML file found for this story"
            })

        # Use the first HTML file
        html_filename = html_files[0]
        html_path = Path(story_data["output_directory"]) / html_filename

        if not html_path.exists():
            return json.dumps({
                "success": False,
                "error": f"HTML file not found: {html_path}"
            })

        # Open in browser
        browser_result = await open_file_in_browser(str(html_path))

        if ctx:
            if browser_result["success"]:
                await ctx.info(f"✅ Story opened successfully: {html_path}")
            else:
                await ctx.warning(f"⚠️ Failed to open story: {browser_result.get('error', 'Unknown error')}")

        return json.dumps({
            "success": browser_result["success"],
            "message": browser_result.get("message", ""),
            "error": browser_result.get("error", ""),
            "html_path": str(html_path),
            "story_id": story_id,
        }, indent=2)

    except Exception as e:
        error_msg = f"Failed to open story in browser: {e!s}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "story_id": story_id,
        })


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
                        "html_path": str(html_files[0]) if html_files else None,
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
        story_details = await get_story_details(story_id)
        story_info = json.loads(story_details)

        if not story_info.get("success"):
            return f"<div class='error'>Error: {story_info.get('error', 'Unknown error')}</div>"

        story_data = story_info["story_data"]

        if ctx:
            await ctx.info(f"📖 Displaying story: {story_data.get('original_prompt', 'Unknown')}")
            story_output_directory = story_data.get("output_directory")
            if ctx and story_output_directory:
                # Log the specific directory being used for this artifact.
                # story_output_directory is typically like "generated_stories/story_id_xxxx"
                await ctx.info(f"Preparing artifact based on content from: {story_output_directory}")
            elif not story_output_directory:
                # This case should ideally not be hit if get_story_details was successful
                # and populated story_data correctly.
                logger.warning(f"Story {story_id}: Output directory missing in metadata for artifact display.")
        html_content = _build_story_artifact_html(story_id, story_data)
        logger.info(f"Generated artifact for story {story_id}")
        return html_content

    except Exception as e:
        error_msg = f"Failed to create story artifact: {e!s}"
        logger.error(error_msg, exc_info=True)
        return f"<div class='error' style='color: red; padding: 20px; text-align: center;'>Error: {error_msg}</div>"

def _build_story_artifact_html(story_id: str, story_data: dict) -> str:
    """Helper to build the HTML artifact for a story."""
    header = _artifact_header(story_id, story_data)
    stats = _artifact_stats(story_data)
    scenes_html = _artifact_scenes(story_id, story_data)
    footer = _artifact_footer(story_id, story_data)
    return header + stats + scenes_html + footer

def _artifact_header(story_id: str, story_data: dict) -> str:
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
        .browser-open-info {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            font-size: 0.95rem;
            text-align: center;
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
    <div class="story-header">
        <div class="story-title">📚 {story_data.get('original_prompt', 'AI Story')}</div>
        <div class="story-meta">
            <div>👤 {story_data.get('character_name') or 'Auto-chosen'}</div>
            <div>🎨 {story_data.get('style', 'cartoon').title()} Style</div>
            <div>📍 {story_data.get('setting') or 'Auto-chosen'}</div>
            <div>🎬 {story_data.get('num_scenes', 0)} Scenes</div>
        </div>
        <div class="browser-open-info">
            💡 To open this story in your browser with full resolution images:<br>
            Use <strong>open_story_in_browser(story_id="{story_id}")</strong><br>
            File location: {story_data.get('html_files', [''])[0] if story_data.get('html_files') else 'N/A'}
        </div>
    </div>
"""

def _artifact_stats(story_data: dict) -> str:
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

def _artifact_scenes(story_id: str, story_data: dict) -> str:
    text_scenes = {}
    image_scenes = {}
    for scene in story_data.get("scenes", []):
        scene_num = scene.get("scene_number")
        if scene.get("type") == "text":
            if scene_num not in text_scenes:
                text_scenes[scene_num] = []
            text_scenes[scene_num].append(scene.get("content", ""))
        elif scene.get("type") == "image":
            image_scenes[scene_num] = scene

    scene_numbers = sorted(
        set(list(text_scenes.keys()) + list(image_scenes.keys()))
    )
    actual_scenes = [sn for sn in scene_numbers if isinstance(sn, int)][:3]

    html = ""
    for scene_num in actual_scenes:
        html += '    <div class="scene">\n'
        html += f'        <div class="scene-number">🎬 Scene {scene_num}</div>\n'
        if scene_num in image_scenes:
            image_scene = image_scenes[scene_num]
            html += f'        <div style="color: #999; text-align: center; padding: 40px; border: 2px dashed #ddd; border-radius: 10px; margin: 20px 0;">🎨 Scene {scene_num} Image: {image_scene.get("filename", "unknown")}<br><small>Full resolution images available in browser version</small></div>\n'
        if scene_num in text_scenes:
            for text_content in text_scenes[scene_num]:
                if text_content.strip():
                    paragraphs = text_content.split('\n\n')
                    for paragraph in paragraphs:
                        if paragraph.strip():
                            html += f'        <div class="scene-text">{paragraph.strip()}</div>\n'
        html += '    </div>\n\n'

    if len(actual_scenes) < len(scene_numbers):
        remaining = len(scene_numbers) - len(actual_scenes)
        html += f"""
    <div class="scene" style="text-align: center; background: rgba(103, 126, 234, 0.1);">
        <div class="scene-number">📚 {remaining} More Scenes Available</div>
        <div class="scene-text" style="text-indent: 0;">
            Open the full story in your browser to see all {story_data.get('num_scenes', 0)} scenes with high-resolution images!<br>
            <strong>Use:</strong> open_story_in_browser(story_id="{story_id}")
        </div>
    </div>
"""
    return html

def _artifact_footer(story_id: str, story_data: dict) -> str:
    return f"""
    <div class="generated-info">
        <p>✨ Generated with Google Gemini AI via Enhanced MCP Server ✨</p>
        <p>Created: {story_data.get('generated_at', 'Unknown date')}</p>
        <p>Model: {story_data.get('model', 'gemini-2.0-flash-preview-image-generation')}</p>
        <p>Story ID: {story_id}</p>
        <p><strong>🌐 For full experience with all images: open_story_in_browser(story_id="{story_id}")</strong></p>
    </div>
</body>
</html>
"""


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
@mcp.resource("guidance://enhanced-story-generation")
def get_enhanced_story_guidance() -> str:
    """Comprehensive guide for using the Enhanced Gemini Picture Book Generator."""
    return """# Enhanced Gemini Picture Book Generator - User Guide

## 🎨 Overview
This enhanced MCP server provides AI-powered story generation using Google's Gemini API with AUTO-OPEN browser functionality. Create unlimited picture books with custom scenes, characters, and art styles that open automatically in your browser!

## 🚀 Quick Start

### 1. Generate a Story (Auto-Opens in Browser!)
```
generate_story(
    story_prompt="A robot learning to paint masterpieces",
    num_scenes=6,
    character_name="Artie",
    setting="art studio",
    style="cartoon",
    auto_open=True  # ← NEW! Auto-opens in browser
)
```

### 2. Open Any Existing Story in Browser
```
open_story_in_browser(story_id="story_20250607_143022_123456")
```

### 3. View Generated Stories
```
list_generated_stories(limit=10)
```

### 4. Display as Artifact (Preview)
```
display_story_as_artifact(story_id="story_20250607_143022_123456")
```

## 🆕 NEW FEATURES

### Auto-Open in Browser
- Stories automatically open in your default browser
- Full resolution images and proper formatting
- Cross-platform support (Linux, macOS, Windows)
- Can be disabled with `auto_open=False`

### Enhanced Story Management
- Direct browser opening for any existing story
- Better file path handling
- Improved artifact previews with browser open instructions

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
- **Auto-open in browser** (NEW!)

### Export Formats
- HTML with embedded images (auto-opens!)
- PDF for easy sharing
- JSON metadata for programmatic access

## ⏱️ Generation Times
- **3 scenes**: ~18 seconds + auto-open
- **6 scenes**: ~36 seconds + auto-open
- **12 scenes**: ~1.2 minutes + auto-open
- **25 scenes**: ~2.5 minutes + auto-open
- **50 scenes**: ~5 minutes + auto-open
- **100 scenes**: ~10 minutes + auto-open

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
│   ├── story.html  ← Auto-opens in browser!
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

3. **Browser Won't Open**
   - Check if `xdg-open` (Linux), `open` (macOS), or `start` (Windows) is available
   - Try `auto_open=False` and open manually
   - Use `open_story_in_browser()` for existing stories

4. **Out of Quota**
   - Free tier: 1,500 requests/day
   - Wait 24 hours or upgrade plan

5. **Images Not Generating**
   - Check API quota
   - Verify image generation model access

### Getting Help
Use `test_gemini_connection()` to diagnose API issues.

## 🎉 Example Workflows

### Auto-Open Test Story
```python
# Generate and auto-open a simple story
result = await generate_story(
    story_prompt="A cat who becomes a superhero",
    num_scenes=3,
    style="cartoon",
    auto_open=True  # Story opens automatically!
)
```

### Epic Adventure with Auto-Open
```python
# Create a long-form story that opens when complete
result = await generate_story(
    story_prompt="The chronicles of a young wizard saving multiple realms",
    num_scenes=50,
    character_name="Luna Stardust",
    setting="magical multiverse",
    style="fantasy art",
    auto_open=True
)
```

### Gallery Management with Browser Opening
```python
# List all stories
stories = await list_generated_stories(limit=20)

# Open any story in browser
await open_story_in_browser("story_20250607_143022_123456")

# Preview in artifact first
await display_story_as_artifact("story_20250607_143022_123456")
```

### Disable Auto-Open for Batch Generation
```python
# Generate multiple stories without opening each one
for prompt in story_prompts:
    await generate_story(
        story_prompt=prompt,
        num_scenes=6,
        auto_open=False  # Don't open each one
    )

# Then open your favorite later
await open_story_in_browser("story_20250607_143022_123456")
```

## 🌟 Pro Tips
1. **Auto-open is ON by default**: Stories open automatically when complete
2. **Turn off auto-open for batch jobs**: Use `auto_open=False` when generating many stories
3. **Open existing stories anytime**: Use `open_story_in_browser(story_id)`
4. **Preview first**: Use `display_story_as_artifact()` for quick preview
5. **Check browser support**: All major browsers supported on Linux/macOS/Windows
6. **Manual opening**: If auto-open fails, find HTML file in output directory

## 📚 Story Examples

### Children's Bedtime Story (Auto-Opens)
```
generate_story(
    story_prompt="A sleepy bunny who helps other forest animals find their way home",
    num_scenes=6,
    character_name="Rosie",
    setting="peaceful meadow",
    style="watercolor",
    auto_open=True
)
```

### Adventure Epic (Auto-Opens When Done)
```
generate_story(
    story_prompt="A space explorer discovering ancient alien mysteries across the galaxy",
    num_scenes=25,
    character_name="Captain Nova",
    setting="distant star systems",
    style="digital art",
    auto_open=True
)
```

### Educational Story (Silent Generation)
```
generate_story(
    story_prompt="A young scientist learning about the water cycle through magical adventures",
    num_scenes=12,
    character_name="Dr. Maya",
    setting="nature laboratory",
    style="realistic",
    auto_open=False  # Generate quietly
)
# Open later with: open_story_in_browser(story_id)
```

## 🚀 NEW Tool Commands

### Auto-Open Generation
```python
generate_story(
    story_prompt="Your story idea",
    num_scenes=6,
    auto_open=True  # Default is True
)
```

### Manual Browser Opening
```python
open_story_in_browser(story_id="story_20250607_143022_123456")
```

### Enhanced Story Listing
```python
stories = list_generated_stories(limit=20)
# Now includes html_path for easy browser opening
```

Ready to create amazing stories that open automatically in your browser? Start with `generate_story()` and watch your imagination come to life! 🚀✨🌐
"""


# Prompts for guided story creation (enhanced)
@mcp.prompt()
def create_enhanced_story_prompt(
    theme: str = "adventure",
    audience: str = "children",
    length: str = "short",
    auto_open: bool = True,
) -> str:
    """Generate an enhanced story prompt with auto-open feature."""

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

    return f"""Create a {audience}-friendly story about {theme_desc} with AUTO-OPEN functionality!

Suggested prompt: "A story that teaches {audience} about {theme_desc} through engaging characters and situations."

Recommended settings:
- num_scenes: {min_scenes}-{max_scenes} (for {length} stories)
- style: Choose based on audience and theme
- character_name: Give your protagonist a memorable name
- setting: Create an immersive world for your story
- auto_open: {auto_open} (opens in browser when complete!)

Enhanced usage:
```
generate_story(
    story_prompt="Your creative story idea here...",
    num_scenes={min_scenes},
    character_name="Hero Name",
    setting="Story World",
    style="cartoon",
    auto_open={auto_open}  # ← NEW! Auto-opens in browser
)
```

🆕 NEW FEATURES:
- Stories automatically open in your browser with full-resolution images
- Use `open_story_in_browser(story_id)` to re-open any existing story
- `auto_open=False` to disable for batch generation
- Cross-platform browser support (Linux/macOS/Windows)

Remember: Be descriptive, include emotions, and make it engaging for your target audience!
The story will open automatically in your browser when complete! 🌐✨"""


def main():
    """Main entry point for the enhanced MCP server."""
    try:
        logger.info("🚀 Starting Enhanced Gemini Picture Book Generator MCP Server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        cleanup_processes()


if __name__ == "__main__":
    main()
