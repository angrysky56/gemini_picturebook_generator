#!/usr/bin/env python3
"""
Simple Flask Web UI for AI Story Generator

A lightweight alternative to Streamlit that doesn't use file watchers.
This version is less likely to hit inotify limits.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_from_directory
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import threading
import queue

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'ai_story_generator_secret_key'

# Global variables for story generation
generation_queue = queue.Queue()
generation_results = {}

def setup_client():
    """Initialize the Google GenAI client."""
    api_key = os.getenv('GOOGLE_API_KEY')

    if not api_key or api_key == 'your_google_api_key_here':
        return None

    return genai.Client(api_key=api_key)

def generate_story_background(story_id, client, story_prompt, num_scenes, character_name="", setting="", style="cartoon"):
    """Generate story in background thread."""
    try:
        # Enhanced prompt
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

        # Update status
        generation_results[story_id] = {
            'status': 'generating',
            'progress': 10,
            'message': 'Connecting to Gemini AI...'
        }

        # Use the image generation model
        model = "gemini-2.0-flash-preview-image-generation"

        generation_results[story_id]['message'] = 'Generating story content...'
        generation_results[story_id]['progress'] = 20

        response = client.models.generate_content(
            model=model,
            contents=enhanced_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["Text", "Image"],
                max_output_tokens=8192
            ),
        )

        generation_results[story_id]['progress'] = 40
        generation_results[story_id]['message'] = 'Processing generated content...'

        # Setup output directory
        project_dir = Path(__file__).parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_dir / "flask_stories" / f"story_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        story_data = {
            'id': story_id,
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
            progress = 40 + (i / total_parts) * 50
            generation_results[story_id]['progress'] = int(progress)

            if part.text is not None:
                generation_results[story_id]['message'] = f'Processing story text part {i+1}...'
                story_data['scenes'].append({
                    'type': 'text',
                    'content': part.text,
                    'scene_number': scene_counter if scene_counter <= num_scenes else 'additional',
                    'part_index': i
                })

            elif part.inline_data is not None:
                generation_results[story_id]['message'] = f'Saving scene {scene_counter} image...'

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

        # Save story metadata
        metadata_path = output_dir / "story_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(story_data, f, indent=2)

        generation_results[story_id] = {
            'status': 'complete',
            'progress': 100,
            'message': 'Story generation complete!',
            'data': story_data
        }

    except Exception as e:
        generation_results[story_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Error: {str(e)}',
            'error': str(e)
        }

@app.route('/')
def index():
    """Main page."""
    client = setup_client()
    api_key_configured = client is not None

    return render_template('index.html', api_key_configured=api_key_configured)

@app.route('/generate', methods=['POST'])
def generate_story():
    """Start story generation."""
    client = setup_client()
    if not client:
        return jsonify({'error': 'API key not configured'}), 400

    data = request.json
    if data is None:
        return jsonify({'error': 'Invalid JSON or missing Content-Type header'}), 400
    story_prompt = data.get('story_prompt', '').strip()
    num_scenes = int(data.get('num_scenes', 6))
    character_name = data.get('character_name', '').strip()
    setting = data.get('setting', '').strip()
    style = data.get('style', 'cartoon').strip()

    if not story_prompt:
        return jsonify({'error': 'Story prompt is required'}), 400

    # Generate unique story ID
    story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Start background generation
    thread = threading.Thread(
        target=generate_story_background,
        args=(story_id, client, story_prompt, num_scenes, character_name, setting, style)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'story_id': story_id})

@app.route('/status/<story_id>')
def get_status(story_id):
    """Get generation status."""
    if story_id in generation_results:
        return jsonify(generation_results[story_id])
    else:
        return jsonify({'status': 'not_found'}), 404

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve generated images."""
    # Find the image in any of the story directories
    stories_dir = Path(__file__).parent / "flask_stories"
    for story_dir in stories_dir.glob("story_*"):
        image_path = story_dir / filename
        if image_path.exists():
            return send_from_directory(str(story_dir), filename)
    return "Image not found", 404

if __name__ == '__main__':
    # Create templates directory and HTML template
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)

    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Story Generator</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #4a4a4a;
            margin-bottom: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            box-sizing: border-box;
        }
        .form-group textarea {
            height: 100px;
            resize: vertical;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .generate-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            margin: 20px 0;
        }
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .generate-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .progress-container {
            display: none;
            margin: 20px 0;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s ease;
        }
        .progress-text {
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
        }
        .story-container {
            display: none;
            margin-top: 30px;
        }
        .scene {
            background: #f9f9f9;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }
        .scene h3 {
            color: #667eea;
            margin-top: 0;
        }
        .scene img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 15px 0;
        }
        .scene-text {
            line-height: 1.6;
            color: #555;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #c62828;
        }
        .api-warning {
            background: #fff3e0;
            color: #ef6c00;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #ef6c00;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 AI Story Generator</h1>
            <p>Create amazing stories with AI-generated images</p>
        </div>

        {% if not api_key_configured %}
        <div class="api-warning">
            <strong>⚠️ API Key Required</strong><br>
            Please configure your Google API key in the .env file to use this application.
        </div>
        {% else %}

        <form id="storyForm">
            <div class="form-group">
                <label for="story_prompt">What's your story idea? *</label>
                <textarea id="story_prompt" name="story_prompt" placeholder="e.g., A young dragon learning to fly, A robot discovering emotions, A magical library where books come alive..." required></textarea>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="character_name">Main character name (optional)</label>
                    <input type="text" id="character_name" name="character_name" placeholder="e.g., Luna, Max, Zara...">
                </div>
                <div class="form-group">
                    <label for="setting">Story setting (optional)</label>
                    <input type="text" id="setting" name="setting" placeholder="e.g., enchanted forest, space station...">
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="style">Art style</label>
                    <select id="style" name="style">
                        <option value="cartoon">Cartoon</option>
                        <option value="anime">Anime</option>
                        <option value="realistic">Realistic</option>
                        <option value="watercolor">Watercolor</option>
                        <option value="sketch">Sketch</option>
                        <option value="digital art">Digital Art</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="num_scenes">Number of scenes (3-12)</label>
                    <select id="num_scenes" name="num_scenes">
                        <option value="3">3 scenes (~2 min)</option>
                        <option value="4">4 scenes (~3 min)</option>
                        <option value="5">5 scenes (~3 min)</option>
                        <option value="6" selected>6 scenes (~4 min)</option>
                        <option value="7">7 scenes (~4 min)</option>
                        <option value="8">8 scenes (~5 min)</option>
                        <option value="9">9 scenes (~6 min)</option>
                        <option value="10">10 scenes (~7 min)</option>
                        <option value="11">11 scenes (~8 min)</option>
                        <option value="12">12 scenes (~8 min)</option>
                    </select>
                </div>
            </div>

            <button type="submit" class="generate-btn" id="generateBtn">
                🚀 Generate Story
            </button>
        </form>

        <div class="progress-container" id="progressContainer">
            <div class="progress-text" id="progressText">Preparing...</div>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
        </div>

        <div class="story-container" id="storyContainer">
            <!-- Story content will be inserted here -->
        </div>

        {% endif %}
    </div>

    <script>
        let currentStoryId = null;
        let pollInterval = null;

        document.getElementById('storyForm').addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(e.target);
            const data = {
                story_prompt: formData.get('story_prompt'),
                character_name: formData.get('character_name'),
                setting: formData.get('setting'),
                style: formData.get('style'),
                num_scenes: formData.get('num_scenes')
            };

            // Start generation
            fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.error) {
                    showError(result.error);
                } else {
                    currentStoryId = result.story_id;
                    startPolling();
                    showProgress();
                }
            })
            .catch(error => {
                showError('Failed to start generation: ' + error.message);
            });
        });

        function showProgress() {
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('generateBtn').textContent = '⏳ Generating...';
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('storyContainer').style.display = 'none';
        }

        function hideProgress() {
            document.getElementById('generateBtn').disabled = false;
            document.getElementById('generateBtn').textContent = '🚀 Generate Story';
            document.getElementById('progressContainer').style.display = 'none';
        }

        function startPolling() {
            pollInterval = setInterval(() => {
                fetch(`/status/${currentStoryId}`)
                    .then(response => response.json())
                    .then(status => {
                        updateProgress(status);

                        if (status.status === 'complete') {
                            clearInterval(pollInterval);
                            hideProgress();
                            displayStory(status.data);
                        } else if (status.status === 'error') {
                            clearInterval(pollInterval);
                            hideProgress();
                            showError(status.message);
                        }
                    })
                    .catch(error => {
                        console.error('Polling error:', error);
                    });
            }, 2000); // Poll every 2 seconds
        }

        function updateProgress(status) {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');

            progressFill.style.width = status.progress + '%';
            progressText.textContent = status.message || 'Processing...';
        }

        function displayStory(storyData) {
            const container = document.getElementById('storyContainer');
            container.innerHTML = '';

            // Story header
            const header = document.createElement('div');
            header.innerHTML = `
                <h2>🎨 ${storyData.original_prompt}</h2>
                <p><strong>Character:</strong> ${storyData.character_name || 'Auto-chosen'} |
                   <strong>Setting:</strong> ${storyData.setting || 'Auto-chosen'} |
                   <strong>Style:</strong> ${storyData.style}</p>
            `;
            container.appendChild(header);

            // Group scenes
            const textScenes = {};
            const imageScenes = {};

            storyData.scenes.forEach(scene => {
                const sceneNum = scene.scene_number;
                if (scene.type === 'text') {
                    if (!textScenes[sceneNum]) {
                        textScenes[sceneNum] = [];
                    }
                    textScenes[sceneNum].push(scene.content);
                } else if (scene.type === 'image') {
                    imageScenes[sceneNum] = scene;
                }
            });

            // Display scenes
            const sceneNumbers = [...new Set([...Object.keys(textScenes), ...Object.keys(imageScenes)])]
                .filter(num => !isNaN(num))
                .sort((a, b) => parseInt(a) - parseInt(b));

            sceneNumbers.forEach(sceneNum => {
                const sceneDiv = document.createElement('div');
                sceneDiv.className = 'scene';

                let sceneHTML = `<h3>🎬 Scene ${sceneNum}</h3>`;

                // Add image
                if (imageScenes[sceneNum]) {
                    sceneHTML += `<img src="/images/${imageScenes[sceneNum].filename}" alt="Scene ${sceneNum}">`;
                }

                // Add text
                if (textScenes[sceneNum]) {
                    textScenes[sceneNum].forEach(text => {
                        sceneHTML += `<div class="scene-text">${text.replace(/\n/g, '<br>')}</div>`;
                    });
                }

                sceneDiv.innerHTML = sceneHTML;
                container.appendChild(sceneDiv);
            });

            container.style.display = 'block';
        }

        function showError(message) {
            const container = document.getElementById('storyContainer');
            container.innerHTML = `<div class="error"><strong>Error:</strong> ${message}</div>`;
            container.style.display = 'block';
        }
    </script>
</body>
</html>
    """

    with open(templates_dir / "index.html", 'w') as f:
        f.write(html_template)

    print("🌐 Starting Flask Web UI...")
    print("📱 Open your browser to: http://localhost:8080")

    app.run(host='0.0.0.0', port=8080, debug=False)
