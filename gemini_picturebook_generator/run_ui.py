#!/usr/bin/env python3
"""
Main entry point for Gemini Picture Book Generator Flask UI.

This module provides a simple way to start the Flask web interface.

Author: Assistant
Date: 2025-06-07
Version: 2.1.0 - Package Edition
"""

from .flask_ui import main as flask_main


def main():
    """Start the Flask web UI."""
    flask_main()


if __name__ == "__main__":
    main()
