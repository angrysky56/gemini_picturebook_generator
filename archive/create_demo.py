#!/usr/bin/env python3
"""
Demo Treasure Story Generator

This creates a demo HTML page showing what the treasure hunt story would look like
with placeholder content, so you can see the styling and layout before getting an API key.
"""

from pathlib import Path
from datetime import datetime


def create_demo_story():
    """Create demo story data with placeholder content."""
    return {
        'scenes': [
            {
                'type': 'text',
                'content': "**Scene 1: The Discovery**\n\nIn a dusty old attic, young Captain Whiskers the cat was exploring boxes left by his grandmother. As sunlight streamed through a cracked window, something glinted beneath a pile of old books. With careful paws, he uncovered a rolled-up parchment with mysterious markings - it was an ancient treasure map! The map showed winding paths through jungles, across rivers, and up mountains, with a large 'X' marking the spot where incredible riches awaited.",
                'scene_number': 1
            },
            {
                'type': 'image',
                'filename': 'placeholder_scene_01.png',
                'path': 'placeholder_scene_01.png',
                'scene_number': 1
            },
            {
                'type': 'text',
                'content': "**Scene 2: Preparing for Adventure**\n\nCaptain Whiskers knew this was the adventure of a lifetime! He gathered his supplies: a sturdy backpack, a compass that belonged to his grandfather, a water bottle, some fish treats for energy, and most importantly, his lucky red bandana. He studied the map carefully, tracing the route with his claw. The first destination was the Whispering Woods, where the map indicated a hidden cave entrance.",
                'scene_number': 2
            },
            {
                'type': 'image',
                'filename': 'placeholder_scene_02.png',
                'path': 'placeholder_scene_02.png',
                'scene_number': 2
            },
            {
                'type': 'text',
                'content': "**Scene 3: Into the Whispering Woods**\n\nThe Whispering Woods lived up to their name - every leaf seemed to murmur secrets as Captain Whiskers ventured deeper. Following the map's directions, he found the cave entrance hidden behind a curtain of hanging vines. Inside, glowing crystals lit the way, and ancient symbols on the walls matched those on his map. He discovered the first clue: a riddle carved in stone that would lead him to the next location.",
                'scene_number': 3
            },
            {
                'type': 'image',
                'filename': 'placeholder_scene_03.png',
                'path': 'placeholder_scene_03.png',
                'scene_number': 3
            },
            {
                'type': 'text',
                'content': "**Scene 4: The Rushing River Challenge**\n\nSolving the riddle led Captain Whiskers to the banks of Roaring Rapids River. The map showed he needed to cross, but the water was swift and deep. Thinking cleverly, he noticed fallen logs and stepping stones. With careful balance and his natural cat agility, he leaped from stone to stone, log to log, until he reached the other side where another clue awaited - a golden key hidden in the roots of an ancient oak tree.",
                'scene_number': 4
            },
            {
                'type': 'image',
                'filename': 'placeholder_scene_04.png',
                'path': 'placeholder_scene_04.png',
                'scene_number': 4
            },
            {
                'type': 'text',
                'content': "**Scene 5: The Mountain Peak Mystery**\n\nThe golden key led Captain Whiskers up Crystal Peak Mountain to a mysterious door built into the rockface. As he inserted the key, the door creaked open to reveal a chamber filled with puzzles and traps. Using his wit and agility, he solved spinning wheel puzzles, avoided swinging pendulums, and navigated through a maze of mirrors. Each puzzle solved revealed part of the final location of the treasure.",
                'scene_number': 5
            },
            {
                'type': 'image',
                'filename': 'placeholder_scene_05.png',
                'path': 'placeholder_scene_05.png',
                'scene_number': 5
            },
            {
                'type': 'text',
                'content': "**Scene 6: The Treasure Discovery**\n\nFollowing the final clues, Captain Whiskers arrived at a beautiful hidden valley where waterfalls cascaded into rainbow pools. There, beneath the largest waterfall, was a cave entrance marked with the same symbol as his map. Inside, he found not just gold and jewels, but something even more valuable - ancient scrolls containing the wisdom and stories of generations past. Captain Whiskers realized the real treasure was the knowledge and confidence he'd gained on his journey, though the gold would certainly help him share more adventures with friends!",
                'scene_number': 6
            },
            {
                'type': 'image',
                'filename': 'placeholder_scene_06.png',
                'path': 'placeholder_scene_06.png',
                'scene_number': 6
            }
        ],
        'generated_at': datetime.now().isoformat(),
        'model': 'demo-placeholder'
    }


def create_placeholder_images(output_dir):
    """Create colorful placeholder images for the demo."""
    from PIL import Image, ImageDraw, ImageFont

    # Scene descriptions for placeholders
    scene_descriptions = [
        "Cat discovers treasure map in attic",
        "Cat preparing adventure supplies",
        "Cat exploring magical cave",
        "Cat crossing rushing river",
        "Cat solving mountain puzzles",
        "Cat finding the treasure"
    ]

    # Colors for each scene
    scene_colors = [
        '#8B4513',  # Brown for attic
        '#228B22',  # Green for preparation
        '#4B0082',  # Purple for cave
        '#1E90FF',  # Blue for river
        '#FF6347',  # Red-orange for mountain
        '#FFD700'   # Gold for treasure
    ]

    for i in range(6):
        # Create image
        img = Image.new('RGB', (800, 600), scene_colors[i])
        draw = ImageDraw.Draw(img)

        # Try to use a default font, fall back to default if not available
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except OSError:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Add title
        title = f"Scene {i+1}"
        title_bbox = draw.textbbox((0, 0), title, font=font_large)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((800-title_width)//2, 150), title, fill='white', font=font_large)

        # Add description
        desc = scene_descriptions[i]
        desc_bbox = draw.textbbox((0, 0), desc, font=font_small)
        desc_width = desc_bbox[2] - desc_bbox[0]
        draw.text(((800-desc_width)//2, 220), desc, fill='white', font=font_small)

        # Add placeholder text
        placeholder_text = "[AI-Generated Image Would Appear Here]"
        placeholder_bbox = draw.textbbox((0, 0), placeholder_text, font=font_small)
        placeholder_width = placeholder_bbox[2] - placeholder_bbox[0]
        draw.text(((800-placeholder_width)//2, 400), placeholder_text, fill='white', font=font_small)

        # Save image
        filename = f"placeholder_scene_{i+1:02d}.png"
        img.save(output_dir / filename, 'PNG')
        print(f"Created placeholder: {filename}")

def create_html_display(story_data, output_dir):
    """Create HTML display for the demo story."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Treasure Hunt Adventure Story - Demo</title>
    <style>
        body {
            font-family: 'Comic Sans MS', cursive, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #f5deb3, #daa520);
            min-height: 100vh;
        }
        .header {
            text-align: center;
            color: #8b4513;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }
        .demo-notice {
            background: rgba(255, 193, 7, 0.9);
            border: 2px solid #ff6347;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
            color: #8b4513;
            font-weight: bold;
        }
        .scene {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            margin: 20px 0;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            border: 3px solid #daa520;
        }
        .scene-image {
            width: 100%;
            max-width: 600px;
            height: auto;
            border-radius: 10px;
            border: 2px solid #8b4513;
            margin: 15px 0;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        .scene-text {
            font-size: 16px;
            line-height: 1.6;
            color: #2f4f4f;
            text-align: justify;
        }
        .scene-number {
            color: #b8860b;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .generated-info {
            text-align: center;
            font-size: 12px;
            color: #696969;
            margin-top: 30px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 10px;
        }
        .api-info {
            background: rgba(135, 206, 235, 0.9);
            border: 2px solid #4169e1;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            color: #2f4f4f;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏴‍☠️ Treasure Hunt Adventure 🏴‍☠️</h1>
        <h2>Demo Story with Placeholder Images</h2>
    </div>

    <div class="demo-notice">
        🎨 This is a DEMO version with placeholder images! 🎨<br>
        With a Google API key, the real version will generate unique, vibrant cartoon images for each scene.
    </div>

    <div class="api-info">
        <h3>🔑 To Generate Real AI Images:</h3>
        <ol>
            <li>Get a Google API key from <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a></li>
            <li>Set the environment variable: <code>export GOOGLE_API_KEY="your-key-here"</code></li>
            <li>Run the main script: <code>python treasure_story_generator.py</code></li>
        </ol>
    </div>
"""

    # Group scenes by number for proper ordering
    text_scenes = {}
    image_scenes = {}

    for scene in story_data['scenes']:
        scene_num = scene['scene_number']
        if scene['type'] == 'text':
            text_scenes[scene_num] = scene['content']
        elif scene['type'] == 'image':
            image_scenes[scene_num] = scene

    # Generate HTML for each scene
    for i in range(1, 7):  # 6 scenes
        if i in text_scenes or i in image_scenes:
            html_content += '    <div class="scene">\n'
            html_content += f'        <div class="scene-number">Scene {i}</div>\n'

            if i in image_scenes:
                image_scene = image_scenes[i]
                html_content += f'        <img src="{image_scene["filename"]}" alt="Scene {i}" class="scene-image">\n'

            if i in text_scenes:
                # Split text into paragraphs and handle markdown-style bold
                text = text_scenes[i].replace('**', '<strong>').replace('**', '</strong>')
                paragraphs = text.split('\n\n')
                for paragraph in paragraphs:
                    if paragraph.strip():
                        # Simple markdown processing
                        paragraph = paragraph.replace('**', '<strong>').replace('**', '</strong>')
                        html_content += f'        <div class="scene-text">{paragraph.strip()}</div>\n'

            html_content += '    </div>\n\n'

    html_content += f"""
    <div class="generated-info">
        <p>Demo generated on: {story_data['generated_at']}</p>
        <p>Model: {story_data['model']} (placeholder content)</p>
        <p>✨ Ready for real AI generation with Google Gemini ✨</p>
    </div>
</body>
</html>
"""

    html_path = output_dir / "treasure_story_demo.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return str(html_path)


def main():
    """Main function to create the demo."""
    print("🏴‍☠️ Creating Treasure Hunt Story Demo! 🏴‍☠️")
    print("=" * 50)

    # Setup output directory
    project_dir = Path(__file__).parent
    output_dir = project_dir / "demo_story"
    output_dir.mkdir(exist_ok=True)

    try:
        # Create demo story data
        story_data = create_demo_story()

        # Create placeholder images
        print("🎨 Creating placeholder images...")
        create_placeholder_images(output_dir)

        # Create HTML display
        html_path = create_html_display(story_data, output_dir)
        print(f"📄 Demo HTML created: {html_path}")

        print(f"\n📂 Demo files saved in: {output_dir}")
        print("\n🎉 Demo treasure hunt story is ready!")
        print(f"Open {html_path} in your browser to see the preview.")

        return story_data

    except Exception as e:
        print(f"❌ Error creating demo: {e}")
        return None


if __name__ == "__main__":
    main()
