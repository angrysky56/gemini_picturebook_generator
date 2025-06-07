#!/usr/bin/env python3
"""
Quick launcher for the modern Flask UI
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the Flask UI with proper environment."""
    project_dir = Path(__file__).parent
    
    print("🚀 Launching Modern AI Story Generator UI...")
    print("✨ Unlimited scenes, modern design, real-time progress")
    print("🌐 Will open at: http://localhost:8080")
    print()
    
    # Change to project directory
    import os
    os.chdir(project_dir)
    
    # Run with virtual environment python
    venv_python = project_dir / "venv" / "bin" / "python"
    
    if venv_python.exists():
        subprocess.run([str(venv_python), "flask_ui.py"])
    else:
        print("❌ Virtual environment not found. Please run:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate") 
        print("   pip install -r requirements.txt")

if __name__ == "__main__":
    main()
