#!/usr/bin/env python3
"""
Enhanced Treasure Story Generator with Image Generation

This script generates customizable stories with AI-generated images using Google's Gemini AI.
Now supports dotenv for API key management and enhanced customization options.

Author: Assistant
Date: 2025-06-07
Version: 2.0 - Fixed API issues and improved error handling
"""

import json
import os
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

try:
    from weasyprint import CSS, HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


def setup_client():
    """
    Initialize the Google GenAI client with API key from environment or .env file.

    Returns:
        genai.Client: Configured client instance

    Raises:
        ValueError: If API key is not found
    """
    # Load environment variables from .env file
    load_dotenv()

    # Try to get API key from environment variable
    api_key = os.getenv('GOOGLE_API_KEY')

    if not api_key or api_key == 'your_google_api_key_here':
        print("⚠️  Google API key not found or not configured properly.")
        print("Please update the .env file with your actual API key.")
        print("Get your API key from: https://aistudio.google.com/app/apikey")
        api_key = input("Or enter your Google API key now: ").strip()

    if not api_key:
        raise ValueError("API key is required to use the image generation service")

    try:
        client = genai.Client(api_key=api_key)
        print("✅ Successfully connected to Google Gemini API")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize Gemini client: {e}")
        raise


def generate_custom_story_with_images(client, story_prompt, num_scenes, output_dir, delay_between_requests=6):
    """
    Generate a custom story with images based on user input.

    Args:
        client (genai.Client): Configured GenAI client
        story_prompt (str): User-defined story prompt
        num_scenes (int): Number of scenes to generate
        output_dir (Path): Directory to save images
        delay_between_requests (int): Seconds to wait between requests (rate limiting)

    Returns:
        dict: Story data with text and image paths
    """
    # Use the image generation model
    model = "gemini-2.0-flash-preview-image-generation"

    # Enhanced prompt for better story generation
    full_prompt = f"""
    You are an expert storyteller and illustrator creating a captivating picture book.

    Create a {num_scenes}-scene story based on this idea: "{story_prompt}"

    Requirements:
    - Each scene should advance the story and be distinct
    - Include vivid, engaging descriptions suitable for illustration
    - Make it artistic, engaging, and age-appropriate
    - Generate both descriptive text and a corresponding image for each scene
    - Keep each scene description between 2-4 sentences

    Please create exactly {num_scenes} scenes, each with descriptive text and an accompanying image.
    Structure: Scene 1: [description], Scene 2: [description], etc.
    """

    print(f"🎨 Generating custom story: '{story_prompt}'")
    print(f"📊 Scenes to generate: {num_scenes}")
    print("⏳ This may take several minutes due to rate limiting...")
    print("⏱️  Rate limit: ~6 seconds between requests (10/minute limit)")

    try:
        print("🔄 Making API request...")

        # Create the configuration properly
        config = types.GenerateContentConfig(
            response_modalities=["Text", "Image"],
            max_output_tokens=8192
        )

        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=config
        )

        # Debug: Print response structure
        print("🔍 API Response received, processing...")

        if not response:
            raise ValueError("No response received from API")

        if not hasattr(response, 'candidates') or not response.candidates:
            raise ValueError("No candidates in API response")

        if not response.candidates[0]:
            raise ValueError("First candidate is empty")

        if not hasattr(response.candidates[0], 'content') or not response.candidates[0].content:
            raise ValueError("No content in first candidate")

        if not hasattr(response.candidates[0].content, 'parts') or not response.candidates[0].content.parts:
            raise ValueError("No parts in content")

        story_data = {
            'scenes': [],
            'generated_at': datetime.now().isoformat(),
            'model': model,
            'original_prompt': story_prompt,
            'num_scenes': num_scenes,
            'total_parts': len(response.candidates[0].content.parts)
        }

        scene_counter = 1
        total_parts = len(response.candidates[0].content.parts)

        print(f"📦 Processing {total_parts} parts from API response...")

        for i, part in enumerate(response.candidates[0].content.parts):
            print(f"🔄 Processing part {i+1}/{total_parts}...")

            if hasattr(part, 'text') and part.text is not None:
                print(f"📖 Found text content (Scene {scene_counter})")
                MAX_TEXT_PREVIEW_LENGTH = 200
                text_preview = part.text[:MAX_TEXT_PREVIEW_LENGTH] + "..." if len(part.text) > MAX_TEXT_PREVIEW_LENGTH else part.text
                print(f"   Preview: {text_preview}")

                story_data['scenes'].append({
                    'type': 'text',
                    'content': part.text,
                    'scene_number': scene_counter if scene_counter <= num_scenes else 'additional',
                    'part_index': i
                })

            elif hasattr(part, 'inline_data') and part.inline_data is not None:
                print(f"🖼️  Found image data (Scene {scene_counter})")

                try:
                    # Save image to file
                    image = Image.open(BytesIO(part.inline_data.data))
                    image_filename = f"scene_{scene_counter:02d}.png"
                    image_path = output_dir / image_filename

                    # Save image with error handling
                    image.save(image_path, 'PNG')
                    print(f"✅ Scene {scene_counter} image saved: {image_filename}")

                    story_data['scenes'].append({
                        'type': 'image',
                        'filename': image_filename,
                        'path': str(image_path),
                        'scene_number': scene_counter,
                        'part_index': i,
                        'image_size': image.size
                    })

                    scene_counter += 1

                    # Rate limiting delay (respect 10 requests per minute)
                    if scene_counter <= num_scenes and i < total_parts - 1:
                        print(f"⏳ Waiting {delay_between_requests} seconds (rate limiting)...")
                        time.sleep(delay_between_requests)

                except Exception as img_error:
                    print(f"❌ Error saving image {scene_counter}: {img_error}")
                    continue
            else:
                print(f"⚠️  Unknown part type at index {i}")

        # Save story metadata
        metadata_path = output_dir / "story_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Generated {scene_counter-1} scene images")
        print(f"📊 Total parts processed: {total_parts}")
        print(f"💾 Metadata saved: {metadata_path}")

        return story_data

    except Exception as e:
        print(f"❌ Error generating story: {e}")
        print(f"🔍 Error type: {type(e).__name__}")

        if "quota" in str(e).lower() or "rate" in str(e).lower():
            print("💡 This might be due to rate limiting. Try again later or reduce the number of scenes.")
        elif "401" in str(e) or "unauthorized" in str(e).lower():
            print("💡 Check your API key - it might be invalid or expired.")
        elif "model" in str(e).lower():
            print("💡 The model might not be available. Try using 'gemini-2.0-flash-lite' instead.")

        return None


def create_html_display(story_data, output_dir):
    """
    Create an HTML file to display the custom story with images.

    Args:
        story_data (dict): Story data with text and images
        output_dir (Path): Directory containing images

    Returns:
        str: Path to HTML file
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Custom AI Story - {story_data.get('original_prompt', 'Adventure')}</title>
    <style>
        body {{
            font-family: 'Comic Sans MS', cursive, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #f0f8ff, #e6e6fa, #f5deb3);
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            color: #4a4a4a;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 15px;
            border: 3px solid #daa520;
        }}
        .story-info {{
            background: rgba(135, 206, 235, 0.9);
            border: 2px solid #4169e1;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            color: #2f4f4f;
        }}
        .scene {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            margin: 20px 0;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            border: 3px solid #daa520;
        }}
        .scene-image {{
            width: 100%;
            max-width: 600px;
            height: auto;
            border-radius: 10px;
            border: 2px solid #8b4513;
            margin: 15px 0;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }}
        .scene-text {{
            font-size: 16px;
            line-height: 1.6;
            color: #2f4f4f;
            text-align: justify;
            margin: 10px 0;
        }}
        .scene-number {{
            color: #b8860b;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .generated-info {{
            text-align: center;
            font-size: 12px;
            color: #696969;
            margin-top: 30px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 10px;
        }}
        .debug-info {{
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Custom AI Story 🎨</h1>
        <h2>"{story_data.get('original_prompt', 'Adventure Story')}"</h2>
    </div>

    <div class="story-info">
        <h3>📖 Story Details:</h3>
        <ul>
            <li><strong>Original Prompt:</strong> {story_data.get('original_prompt', 'N/A')}</li>
            <li><strong>Scenes Requested:</strong> {story_data.get('num_scenes', 'N/A')}</li>
            <li><strong>Total Parts Generated:</strong> {story_data.get('total_parts', 'N/A')}</li>
            <li><strong>Generated:</strong> {story_data.get('generated_at', 'N/A')}</li>
            <li><strong>Model:</strong> {story_data.get('model', 'N/A')}</li>
        </ul>
    </div>
"""

    # Group scenes by number for proper ordering
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

    # Generate HTML for each scene
    scene_numbers = sorted(set(list(text_scenes.keys()) + list(image_scenes.keys())))
    actual_scenes = [sn for sn in scene_numbers if isinstance(sn, int)]

    for scene_num in actual_scenes:
        html_content += '    <div class="scene">\n'
        html_content += f'        <div class="scene-number">Scene {scene_num}</div>\n'

        if scene_num in image_scenes:
            image_scene = image_scenes[scene_num]
            html_content += f'        <img src="{image_scene["filename"]}" alt="Scene {scene_num}" class="scene-image">\n'
            if 'image_size' in image_scene:
                html_content += f'        <div class="debug-info">Image size: {image_scene["image_size"]}</div>\n'

        if scene_num in text_scenes:
            for text_content in text_scenes[scene_num]:
                # Split text into paragraphs for better formatting
                paragraphs = text_content.split('\n\n')
                for paragraph in paragraphs:
                    if paragraph.strip():
                        # Simple markdown-style processing
                        processed_paragraph = paragraph.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                        html_content += f'        <div class="scene-text">{processed_paragraph.strip()}</div>\n'

        html_content += '    </div>\n\n'

    # Add any additional text content
    for scene in story_data['scenes']:
        if scene['type'] == 'text' and scene['scene_number'] == 'additional':
            html_content += '    <div class="scene">\n'
            html_content += '        <div class="scene-number">Additional Content</div>\n'
            html_content += f'        <div class="scene-text">{scene["content"]}</div>\n'
            html_content += '    </div>\n\n'

    html_content += f"""
    <div class="generated-info">
        <p>Generated on: {story_data['generated_at']}</p>
        <p>Model: {story_data['model']}</p>
        <p>Total Parts: {story_data.get('total_parts', 'N/A')}</p>
        <p>✨ Created with Google Gemini AI ✨</p>
    </div>
</body>
</html>
"""

    # Create safe filename
    safe_prompt = "".join(c for c in story_data.get('original_prompt', 'story')[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
    html_filename = f"{safe_prompt.replace(' ', '_')}_story.html"
    html_path = output_dir / html_filename

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return str(html_path)


def create_pdf_from_html(html_path, output_dir):
    """
    Convert HTML story to PDF for easy sharing.
    Now uses enhanced PDF generation with proper page breaks.

    Args:
        html_path (str): Path to the HTML file
        output_dir (Path): Directory to save PDF

    Returns:
        str: Path to PDF file or None if failed
    """
    if not WEASYPRINT_AVAILABLE:
        print("⚠️  WeasyPrint not available. PDF generation skipped.")
        print("   Install with: uv pip install weasyprint")
        return None

    # Import here to avoid unbound variable error
    from weasyprint import CSS, HTML

    try:
        html_file = Path(html_path)
        if not html_file.exists():
            print(f"❌ HTML file not found: {html_path}")
            return None

        # Create PDF filename
        pdf_filename = html_file.stem + '.pdf'
        pdf_path = output_dir / pdf_filename

        print(f"📄 Converting to PDF with enhanced formatting: {pdf_filename}")

        # Convert HTML to PDF with improved settings
        # Enhanced CSS for better PDF formatting
        enhanced_css = CSS(string="""
            @page {
                size: A4;
                margin: 20mm;
            }
            .scene {
                page-break-before: always;
                page-break-inside: avoid;
            }
            .scene-image {
                max-width: 100%;
                max-height: 15cm;
                page-break-inside: avoid;
            }
            body {
                font-family: 'Times New Roman', serif;
                font-size: 12pt;
                line-height: 1.4;
            }
            .header {
                page-break-after: always;
            }
            .story-info {
                page-break-after: always;
            }
            .debug-info {
                display: none;
            }
        """)

        html_doc = HTML(filename=str(html_file))
        html_doc.write_pdf(str(pdf_path), stylesheets=[enhanced_css])
        print(f"✅ Enhanced PDF created: {pdf_path}")
        print("📖 Each scene now starts on a new page for better readability")
        return str(pdf_path)

    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        print("💡 This might be due to missing system dependencies.")
        print("   On Ubuntu/Debian: sudo apt-get install libpango-1.0-0 libharfbuzz0b libcairo-gobject2")
        return None


def test_api_connection():
    """Test API connection and available models."""
    try:
        client = setup_client()

        # Try a simple text-only request first
        test_response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents="Say hello and confirm you're working."
        )

        if test_response and test_response.candidates:
            candidate = test_response.candidates[0]
            if candidate and candidate.content and candidate.content.parts and candidate.content.parts[0].text:
                print("✅ API connection test successful!")
                print(f"🤖 Response: {candidate.content.parts[0].text[:100]}...")
                return True
            else:
                print("❌ API test failed - response structure unexpected or missing text.")
                return False
        else:
            print("❌ API test failed - no response or no candidates")
            return False

    except Exception as e:
        print(f"❌ API connection test failed: {e}")
        return False


def main():
    """Main function to orchestrate the custom story generation process."""
    print("🎨 Welcome to the Enhanced Custom Story Generator! 🎨")
    print("=" * 70)

    # Setup output directory
    project_dir = Path(__file__).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_dir / "generated_stories" / f"story_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Test API connection first
        print("\n🔍 Testing API connection...")
        if not test_api_connection():
            print("❌ API connection failed. Please check your API key and try again.")
            return None

        # Initialize client
        client = setup_client()

        # Get user input for custom story
        print("\n📝 Let's create your custom story!")
        story_prompt = input("What story would you like to create? (e.g., 'A robot learning to paint'): ").strip()

        if not story_prompt:
            story_prompt = "A brave explorer discovering magical creatures in an enchanted forest"
            print(f"Using default story: {story_prompt}")

        num_scenes_input = input("How many scenes? (1-9999+, your choice!): ").strip()
        try:
            num_scenes = int(num_scenes_input)
            if num_scenes < 1:
                num_scenes = 1
                print("Setting minimum: 1 scene")
            # No upper limit - user's choice!
        except ValueError:
            num_scenes = 6
            print("Using default: 6 scenes")

        # Show rate limiting info
        estimated_time = num_scenes * 6 / 60  # 6 seconds per request
        hours = int(estimated_time // 60)
        minutes = int(estimated_time % 60)

        if hours > 0:
            time_str = f"~{hours}h {minutes}m"
        else:
            time_str = f"~{estimated_time:.1f} minutes"

        print(f"\n⏱️  Estimated generation time: {time_str}")
        print("💡 This is due to API rate limits (10 requests/minute)")

        LARGE_STORY_THRESHOLD = 100
        LONG_STORY_THRESHOLD = 50
        if num_scenes > LARGE_STORY_THRESHOLD:
            print(f"🎯 Large story! {num_scenes} scenes will create an epic adventure!")
        elif num_scenes > LONG_STORY_THRESHOLD:
            print(f"📚 Long story! {num_scenes} scenes will make a wonderful book!")

        proceed = input("Continue? (y/n): ").strip().lower()
        if proceed not in ['y', 'yes', '']:
            print("Story generation cancelled.")
            return None

        # Generate story with images
        story_data = generate_custom_story_with_images(client, story_prompt, num_scenes, output_dir)

        if story_data:
            print("\n✅ Story generation completed successfully!")

            # Create HTML display
            html_path = create_html_display(story_data, output_dir)
            print(f"📄 HTML story created: {html_path}")

            # Create PDF version
            pdf_path = create_pdf_from_html(html_path, output_dir)
            if pdf_path:
                print(f"📄 PDF story created: {pdf_path}")

            print(f"\n📂 All files saved in: {output_dir}")
            print("\n🎉 Your custom adventure is ready!")
            print(f"💻 Open {html_path} in your browser to view the story")
            if pdf_path:
                print(f"📱 Share the PDF: {pdf_path}")

            return story_data
        else:
            print("❌ Failed to generate story")
            return None

    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


if __name__ == "__main__":
    main()
