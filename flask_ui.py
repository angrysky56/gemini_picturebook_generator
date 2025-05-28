#!/usr/bin/env python3
"""
Flask Web UI for AI Story Generator

Imports and uses functions from enhanced_story_generator.py
instead of duplicating code, making maintenance much easier.

Author: Assistant
Date: 2025-05-28
"""

import json
import threading
import queue
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from dotenv import load_dotenv

# Import our story generation functions
from enhanced_story_generator import (
    setup_client,
    generate_custom_story_with_images,
    create_html_display,
    create_pdf_from_html
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'ai_story_generator_secret_key'

# Global variables for story generation
generation_queue = queue.Queue()
generation_results = {}

def generate_story_background(story_id, story_prompt, num_scenes, character_name="", setting="", style="cartoon"):
    """Generate story in background thread using imported functions."""
    try:
        # Update status
        generation_results[story_id] = {
            'status': 'generating',
            'progress': 10,
            'message': 'Setting up story generation...'
        }

        # Get client using imported function
        client = setup_client()
        if not client:
            generation_results[story_id] = {
                'status': 'error',
                'progress': 0,
                'message': 'Failed to initialize API client',
                'error': 'API key not configured'
            }
            return

        generation_results[story_id]['progress'] = 20
        generation_results[story_id]['message'] = 'Creating output directory...'

        # Setup output directory with Flask-specific naming
        project_dir = Path(__file__).parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_dir / "generated_stories" / f"story_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        generation_results[story_id]['progress'] = 30
        generation_results[story_id]['message'] = 'Generating story with AI...'

        # Use the imported generation function
        story_data = generate_custom_story_with_images(
            client,
            story_prompt,
            num_scenes,
            output_dir,
            delay_between_requests=6
        )

        if not story_data:
            generation_results[story_id] = {
                'status': 'error',
                'progress': 0,
                'message': 'Story generation failed',
                'error': 'Failed to generate story content'
            }
            return

        # Add extra metadata for web interface
        story_data.update({
            'id': story_id,
            'character_name': character_name,
            'setting': setting,
            'style': style,
            'output_dir': str(output_dir)
        })

        generation_results[story_id]['progress'] = 80
        generation_results[story_id]['message'] = 'Creating HTML and PDF versions...'

        # Create HTML display using imported function
        html_path = create_html_display(story_data, output_dir)
        story_data['html_path'] = html_path

        # Create PDF version using imported function
        pdf_path = create_pdf_from_html(html_path, output_dir)
        if pdf_path:
            story_data['pdf_path'] = pdf_path

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

    # Validate scene count (use same limits as enhanced_story_generator)
    if num_scenes < 1:
        num_scenes = 3
    elif num_scenes > 1400:
        num_scenes = 1400

    # Generate unique story ID
    story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Start background generation
    thread = threading.Thread(
        target=generate_story_background,
        args=(story_id, story_prompt, num_scenes, character_name, setting, style)
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
    stories_dir = Path(__file__).parent / "generated_stories"
    for story_dir in stories_dir.glob("story_*"):
        image_path = story_dir / filename
        if image_path.exists():
            return send_from_directory(str(story_dir), filename)
    return "Image not found", 404

@app.route('/download/<story_id>/<format>')
def download_story(story_id, format):
    """Download story in specified format (html or pdf)."""
    if story_id not in generation_results:
        return "Story not found", 404

    result = generation_results[story_id]
    if result['status'] != 'complete':
        return "Story not ready", 400

    story_data = result['data']

    if format == 'html' and 'html_path' in story_data:
        html_path = Path(story_data['html_path'])
        if html_path.exists():
            return send_file(
                html_path,
                as_attachment=True,
                download_name=f"{story_data.get('original_prompt', 'story')[:30]}.html"
            )
    elif format == 'pdf' and 'pdf_path' in story_data:
        pdf_path = Path(story_data['pdf_path'])
        if pdf_path.exists():
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"{story_data.get('original_prompt', 'story')[:30]}.pdf"
            )

    return "File not found", 404

@app.route('/gallery')
def gallery():
    """Show gallery of all generated stories."""
    stories_dir = Path(__file__).parent / "generated_stories"
    stories = []

    if stories_dir.exists():
        for story_dir in sorted(stories_dir.glob("story_*"), reverse=True):
            metadata_file = story_dir / "story_metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                    # Find HTML file
                    html_files = list(story_dir.glob("*.html"))
                    if html_files:
                        metadata['html_file'] = html_files[0].name

                    # Check for PDF
                    pdf_files = list(story_dir.glob("*.pdf"))
                    if pdf_files:
                        metadata['pdf_file'] = pdf_files[0].name

                    metadata['folder'] = story_dir.name
                    stories.append(metadata)
                except Exception:
                    continue

    return render_template('gallery.html', stories=stories)

if __name__ == '__main__':
    # Create templates directory and HTML templates
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)

    # Enhanced index template with better styling and PDF support
    index_template = """
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
        .nav {
            text-align: center;
            margin-bottom: 20px;
        }
        .nav a {
            color: #667eea;
            text-decoration: none;
            margin: 0 15px;
            font-weight: bold;
        }
        .nav a:hover {
            text-decoration: underline;
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
        .download-section {
            background: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }
        .download-btn {
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            margin: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .download-btn:hover {
            background: #218838;
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
        .rate-limit-info {
            background: #e3f2fd;
            color: #1976d2;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #1976d2;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 AI Story Generator</h1>
            <p>Create amazing stories with AI-generated images</p>
        </div>

        <div class="nav">
            <a href="/">🏠 Generator</a>
            <a href="/gallery">🖼️ Gallery</a>
        </div>

        {% if not api_key_configured %}
        <div class="api-warning">
            <strong>⚠️ API Key Required</strong><br>
            Please configure your Google API key in the .env file to use this application.
        </div>
        {% else %}

        <div class="rate-limit-info">
            <strong>📊 API Limits:</strong> 10 requests/minute, 1,400/day<br>
            <strong>🎯 Max scenes:</strong> Up to 1,400 scenes per story (full daily free allowance!)
        </div>

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
                    <label for="num_scenes">Number of scenes (3-50 recommended)</label>
                    <select id="num_scenes" name="num_scenes">
                        <option value="3">3 scenes (~2 min)</option>
                        <option value="5">5 scenes (~3 min)</option>
                        <option value="6" selected>6 scenes (~4 min)</option>
                        <option value="8">8 scenes (~5 min)</option>
                        <option value="10">10 scenes (~7 min)</option>
                        <option value="15">15 scenes (~10 min)</option>
                        <option value="20">20 scenes (~15 min)</option>
                        <option value="30">30 scenes (~20 min)</option>
                        <option value="50">50 scenes (~35 min)</option>
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

            // Download section
            const downloadSection = document.createElement('div');
            downloadSection.className = 'download-section';
            downloadSection.innerHTML = `
                <h3>📥 Download Your Story</h3>
                <a href="/download/${currentStoryId}/html" class="download-btn">📄 Download HTML</a>
                <a href="/download/${currentStoryId}/pdf" class="download-btn">📄 Download PDF</a>
            `;
            container.appendChild(downloadSection);

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

    # Gallery template
    gallery_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Story Gallery - AI Story Generator</title>
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
        .nav {
            text-align: center;
            margin-bottom: 20px;
        }
        .nav a {
            color: #667eea;
            text-decoration: none;
            margin: 0 15px;
            font-weight: bold;
        }
        .nav a:hover {
            text-decoration: underline;
        }
        .story-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .story-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .story-title {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        .story-meta {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        .story-actions {
            margin-top: 15px;
        }
        .story-actions a {
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            text-decoration: none;
            margin-right: 10px;
            font-size: 0.9em;
        }
        .story-actions a:hover {
            background: #5a6fd8;
        }
        .no-stories {
            text-align: center;
            color: #666;
            margin: 50px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖼️ Story Gallery</h1>
            <p>Your AI-generated stories</p>
        </div>

        <div class="nav">
            <a href="/">🏠 Generator</a>
            <a href="/gallery">🖼️ Gallery</a>
        </div>

        {% if stories %}
            <div class="story-grid">
                {% for story in stories %}
                <div class="story-card">
                    <div class="story-title">{{ story.original_prompt[:50] }}{% if story.original_prompt|length > 50 %}...{% endif %}</div>
                    <div class="story-meta">
                        📊 {{ story.num_scenes }} scenes<br>
                        🎨 {{ story.style or 'cartoon' }} style<br>
                        📅 {{ story.generated_at[:19] }}
                    </div>
                    <div class="story-actions">
                        {% if story.html_file %}
                        <a href="/generated_stories/{{ story.folder }}/{{ story.html_file }}" target="_blank">📄 View</a>
                        {% endif %}
                        {% if story.pdf_file %}
                        <a href="/generated_stories/{{ story.folder }}/{{ story.pdf_file }}" target="_blank">📄 PDF</a>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="no-stories">
                <h3>No stories generated yet</h3>
                <p>Create your first AI story to see it here!</p>
                <a href="/" style="color: #667eea;">🚀 Generate Story</a>
            </div>
        {% endif %}
    </div>
</body>
</html>
    """

    with open(templates_dir / "index.html", 'w') as f:
        f.write(index_template)

    with open(templates_dir / "gallery.html", 'w') as f:
        f.write(gallery_template)

    print("🌐 Starting Refactored Flask Web UI...")
    print("📱 Open your browser to: http://localhost:8080")
    print("🔧 Imports from enhanced_story_generator.py")
    print("📄 Includes PDF generation and story gallery!")

    app.run(host='0.0.0.0', port=8080, debug=False)
