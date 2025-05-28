#!/usr/bin/env python3
"""
Setup script for the AI Story Generator

This script helps set up the .env file with the Google API key from your environment.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def setup_env_file():
    """Set up the .env file with the Google API key."""

    project_dir = Path(__file__).parent
    env_file = project_dir / ".env"

    print("🔑 Setting up your .env file...")

    # Check if API key exists in environment
    existing_key = os.getenv('GOOGLE_API_KEY')

    if existing_key and existing_key != 'your_google_api_key_here':
        print("✅ Found existing Google API key in environment!")

        # Update .env file
        with open(env_file, 'w') as f:
            content = f"""# Google API Configuration
# Generated automatically from environment variable
GOOGLE_API_KEY={existing_key}

# Rate Limiting Information (Free Tier)
# - 10 requests per minute
# - 1,500 requests per day
# Keep this in mind when generating large stories!

# Project Configuration
PROJECT_NAME=AI Story Generator
VERSION=1.0.0
"""
            f.write(content)

        print(f"✅ Updated .env file: {env_file}")
        print("🚀 You're ready to generate stories!")
        return True

    else:
        print("❌ No Google API key found in environment variables.")
        print("\nPlease set up your API key:")
        print("1. Get your API key from: https://aistudio.google.com/app/apikey")
        print("2. Set it as an environment variable:")
        print("   export GOOGLE_API_KEY='your-api-key-here'")
        print("3. Run this setup script again")
        print("\nOr manually edit the .env file to add your key.")
        return False

if __name__ == "__main__":
    setup_env_file()
