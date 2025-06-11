"""
Gemini Picture Book Generator - AI-powered story creation with unlimited scenes and MCP support.

This package provides:
- AI story generation using Google's Gemini API
- Unlimited scene support (no artificial limits)
- Modern Flask web interface
- MCP server for integration with Claude Desktop
- PDF and HTML export capabilities
- Real-time progress tracking

Author: Assistant
Version: 2.1.0
License: MIT
"""

__version__ = "2.1.0"
__author__ = "Assistant"
__license__ = "MIT"

from .enhanced_story_generator import (
    create_html_display,
    create_pdf_from_html,
    generate_custom_story_with_images,
    setup_client,
    test_api_connection,
)
from .flask_ui import app as flask_app

__all__ = [
    "create_html_display",
    "create_pdf_from_html",
    "flask_app",
    "generate_custom_story_with_images",
    "setup_client",
    "test_api_connection",
]
