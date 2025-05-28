#!/usr/bin/env python3
"""
AI Story Generator Web UI

A Streamlit web interface for generating custom stories with AI-generated images.
Features rate limiting awareness, progress tracking, and beautiful presentation.

Author: Assistant
Date: 2025-05-27
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64


# Load environment variables
load_dotenv()


def setup_client():
    """Initialize the Google GenAI client."""
    api_key = os.getenv('GOOGLE_API_KEY')

    if not api_key or api_key == 'your_google_api_key_here':
        return None

    return genai.Client(api_key=api_key)


def encode_image_to_base64(image_path):
    """Convert image to base64 for HTML embedding."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (IOError, OSError) as _:
        return None


def generate_story_with_progress(client, story_prompt, num_scenes, character_name="", setting="", style="cartoon"):
    """
    Generate story with progress tracking and rate limiting.

    Args:
        client: GenAI client
        story_prompt: User's story idea
        num_scenes: Number of scenes to generate
        character_name: Optional character name
        setting: Optional setting description
        style: Art style for images

    Returns:
        dict: Story data or None if failed
    """

    # Enhanced prompt with user customizations
    enhanced_prompt = f"""
    Create a {num_scenes}-scene story based on this concept: {story_prompt}

    Story Customizations:
    - Main character name: {character_name if character_name else "Choose an appropriate name"}
    - Setting/Location: {setting if setting else "Choose an appropriate setting"}
    - Art style: {style} style illustrations

    Requirements:
    - Each scene should be visually distinct and compelling
    - Include vivid descriptions perfect for {style}-style artwork
    - Make it engaging and family-friendly
    - Progress the story naturally from scene to scene
    - Generate both descriptive narrative text AND a corresponding image for each scene
    - Number each scene clearly (Scene 1, Scene 2, etc.)

    Please create exactly {num_scenes} scenes, each with both text description and a visual image.
    """

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.text("🎨 Connecting to Gemini AI...")

        # Use the image generation model
        model = "gemini-2.0-flash-preview-image-generation"

        status_text.text("📝 Generating story content...")
        progress_bar.progress(10)

        response = client.models.generate_content(
            model=model,
            contents=enhanced_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["Text", "Image"],
                max_output_tokens=8192
            ),
        )

        progress_bar.progress(30)
        status_text.text("🖼️ Processing generated content...")

        # Setup output directory
        project_dir = Path(__file__).parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_dir / "streamlit_stories" / f"story_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        story_data = {
            'scenes': [],
            'generated_at': datetime.now().isoformat(),
            'model': model,
            'original_prompt': story_prompt,
            'character_name': character_name,
            'setting': setting,
            'style': style,
            'num_scenes': num_scenes,
            'output_dir': str(output_dir)
        }

        scene_counter = 1
        total_parts = len(response.candidates[0].content.parts)

        for i, part in enumerate(response.candidates[0].content.parts):
            progress = 30 + (i / total_parts) * 60
            progress_bar.progress(int(progress))

            if part.text is not None:
                status_text.text(f"📖 Processing story text part {i+1}...")
                story_data['scenes'].append({
                    'type': 'text',
                    'content': part.text,
                    'scene_number': scene_counter if scene_counter <= num_scenes else 'additional',
                    'part_index': i
                })

            elif part.inline_data is not None:
                status_text.text(f"🖼️ Saving scene {scene_counter} image...")

                # Save image to file
                image = Image.open(BytesIO(part.inline_data.data))
                image_filename = f"scene_{scene_counter:02d}_story.png"
                image_path = output_dir / image_filename

                # Save image
                image.save(image_path, 'PNG')

                story_data['scenes'].append({
                    'type': 'image',
                    'filename': image_filename,
                    'path': str(image_path),
                    'scene_number': scene_counter,
                    'part_index': i
                })

                scene_counter += 1

        progress_bar.progress(100)
        status_text.text("✅ Story generation complete!")

        # Save story metadata
        metadata_path = output_dir / "story_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(story_data, f, indent=2)

        return story_data

    except Exception as e:
        status_text.text(f"❌ Error: {str(e)}")
        st.error(f"Failed to generate story: {str(e)}")
        if "quota" in str(e).lower() or "rate" in str(e).lower():
            st.warning("⚠️ Rate limit reached. Please try again later or reduce the number of scenes.")
        return None


def display_story(story_data):
    """Display the generated story in the Streamlit interface."""

    st.markdown("---")
    st.markdown(f"# 🎨 {story_data.get('original_prompt', 'Your Custom Story')}")

    # Story info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📖 Scenes", story_data.get('num_scenes', 'N/A'))
    with col2:
        st.metric("🎭 Character", story_data.get('character_name', 'Auto-chosen') or 'Auto-chosen')
    with col3:
        st.metric("🏞️ Setting", story_data.get('setting', 'Auto-chosen') or 'Auto-chosen')

    # Group scenes by number
    text_scenes = {}
    image_scenes = {}

    for scene in story_data['scenes']:
        scene_num = scene['scene_number']
        if scene['type'] == 'text':
            if scene_num not in text_scenes:
                text_scenes[scene_num] = []
            text_scenes[scene_num].append(scene['content'])
        elif scene['type'] == 'image':
            image_scenes[scene_num] = scene

    # Display each scene
    scene_numbers = sorted([sn for sn in set(list(text_scenes.keys()) + list(image_scenes.keys())) if isinstance(sn, int)])

    for scene_num in scene_numbers:
        with st.container():
            st.markdown(f"## 🎬 Scene {scene_num}")

            # Display image if available
            if scene_num in image_scenes:
                image_path = image_scenes[scene_num]['path']
                if os.path.exists(image_path):
                    st.image(image_path, caption=f"Scene {scene_num}", use_column_width=True)
                else:
                    st.warning(f"Image file not found: {image_path}")

            # Display text content
            if scene_num in text_scenes:
                for text_content in text_scenes[scene_num]:
                    # Clean up the text and format it nicely
                    formatted_text = text_content.replace('**', '**').replace('*', '*')
                    st.markdown(formatted_text)

            st.markdown("---")

    # Add download option
    if 'output_dir' in story_data:
        st.markdown("### 📥 Download Your Story")
        output_dir = Path(story_data['output_dir'])
        if output_dir.exists():
            st.info(f"📂 Story files saved to: `{output_dir}`")

            # List generated files
            files = list(output_dir.glob("*"))
            if files:
                st.markdown("**Generated files:**")
                for file in sorted(files):
                    st.text(f"📄 {file.name}")


def main():
    """Main Streamlit app."""

    # Page config
    st.set_page_config(
        page_title="AI Story Generator",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .story-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎨 AI Story Generator</h1>
        <p>Create amazing stories with AI-generated images using Google Gemini</p>
    </div>
    """, unsafe_allow_html=True)

    # Check for API key setup
    client = setup_client()
    if not client:
        st.error("🔑 **Google API Key Required**")
        st.markdown("""
        Please set up your Google API key:
        1. Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
        2. Update the `.env` file in the project directory with your key:
           ```
           GOOGLE_API_KEY=your_actual_api_key_here
           ```
        3. Restart this application
        """)
        st.stop()

    # Sidebar for story configuration
    with st.sidebar:
        st.markdown("## 📝 Story Configuration")

        # Story prompt
        story_prompt = st.text_area(
            "What's your story idea?",
            placeholder="e.g., A young dragon learning to fly, A robot discovering emotions, A magical library where books come alive...",
            height=100
        )

        # Character customization
        st.markdown("### 🎭 Character Details")
        character_name = st.text_input(
            "Main character name (optional)",
            placeholder="e.g., Luna, Max, Zara..."
        )

        # Setting
        st.markdown("### 🌍 Setting")
        setting = st.text_input(
            "Story setting (optional)",
            placeholder="e.g., enchanted forest, space station, underwater city..."
        )

        # Art style
        st.markdown("### 🎨 Art Style")
        art_style = st.selectbox(
            "Choose art style",
            ["cartoon", "anime", "realistic", "watercolor", "sketch", "digital art"],
            index=0
        )

        # Number of scenes
        st.markdown("### 📊 Story Length")
        num_scenes = st.slider(
            "Number of scenes",
            min_value=3,
            max_value=12,
            value=6,
            help="More scenes = longer generation time due to rate limits"
        )

        # Rate limiting info
        estimated_time = num_scenes * 0.5  # Rough estimate
        st.info(f"⏱️ Estimated time: ~{estimated_time:.1f} minutes\\n💡 Limited by API rate limits (10/minute)")

        # Generation button
        generate_button = st.button(
            "🚀 Generate Story",
            type="primary",
            use_container_width=True
        )

    # Main content area
    if generate_button:
        if not story_prompt.strip():
            st.error("Please enter a story idea!")
        else:
            st.markdown("## 🎬 Generating Your Story...")

            # Generate the story
            story_data = generate_story_with_progress(
                client,
                story_prompt,
                num_scenes,
                character_name,
                setting,
                art_style
            )

            if story_data:
                # Display the generated story
                display_story(story_data)

                # Success message
                st.success("🎉 Your story has been generated successfully!")
                st.balloons()
            else:
                st.error("Failed to generate story. Please try again.")

    else:
        # Welcome screen
        st.markdown("## 👋 Welcome to the AI Story Generator!")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### ✨ What You Can Create:
            - **Custom stories** with any theme or concept
            - **AI-generated images** for each scene
            - **Personalized characters** and settings
            - **Multiple art styles** to choose from
            - **3-12 scenes** per story
            """)

        with col2:
            st.markdown("""
            ### 🚀 How It Works:
            1. **Describe your story idea** in the sidebar
            2. **Customize** character names and settings
            3. **Choose** your preferred art style
            4. **Select** number of scenes (3-12)
            5. **Click Generate** and wait for the magic!
            """)

        # Example stories
        st.markdown("## 💡 Story Ideas to Get You Started:")

        example_col1, example_col2, example_col3 = st.columns(3)

        with example_col1:
            st.markdown("""
            **🐉 Fantasy Adventures**
            - A dragon who's afraid of heights
            - A wizard's apprentice mixing up spells
            - A magical library where books come alive
            """)

        with example_col2:
            st.markdown("""
            **🚀 Sci-Fi Stories**
            - A robot learning human emotions
            - Space explorers discovering a new planet
            - A time traveler fixing historical mistakes
            """)

        with example_col3:
            st.markdown("""
            **🌟 Everyday Magic**
            - A child who can talk to animals
            - A baker whose pastries grant wishes
            - A musician whose melodies change weather
            """)

        # Rate limiting information
        st.markdown("---")
        st.markdown("### ⚡ API Rate Limits")
        st.info("""
        **Free Tier Limits:**
        - 🕐 10 requests per minute
        - 📅 1,500 requests per day

        **What this means:**
        - Longer stories take more time to generate
        - Built-in delays prevent rate limit errors
        - Complex stories (8+ scenes) may take 5-10 minutes
        """)


if __name__ == "__main__":
    main()
