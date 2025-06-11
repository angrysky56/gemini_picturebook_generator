#!/usr/bin/env python3
"""
Modern Flask Web UI for AI Story Generator - Version 2.1

Complete rewrite with:
- No artificial scene limitations
- Modern responsive design
- Real-time progress tracking
- Better error handling
- Enhanced gallery
- Mobile-friendly interface
- Package structure support

Author: Assistant
Date: 2025-06-07
Version: 2.1.0 - Package Edition
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)

# Import our story generation functions (package imports)
from .enhanced_story_generator import (
    create_html_display,
    create_pdf_from_html,
    generate_custom_story_with_images,
    setup_client,
    test_api_connection,
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'ai_story_generator_unlimited_v21'

# Global variables for story generation
generation_results = {}

def generate_story_background(story_id, story_prompt, num_scenes, character_name="", setting="", style="cartoon"):
    """Generate story in background thread with unlimited scenes."""
    try:
        # Update status
        generation_results[story_id] = {
            'status': 'initializing',
            'progress': 5,
            'message': 'Setting up story generation...',
            'current_scene': 0,
            'total_scenes': num_scenes,
            'scenes_completed': []
        }

        # Test API connection first
        generation_results[story_id]['message'] = 'Testing API connection...'
        generation_results[story_id]['progress'] = 10

        if not test_api_connection():
            generation_results[story_id] = {
                'status': 'error',
                'progress': 0,
                'message': 'API connection failed',
                'error': 'Unable to connect to Gemini API. Check your API key.'
            }
            return

        # Get client
        generation_results[story_id]['message'] = 'Initializing AI client...'
        generation_results[story_id]['progress'] = 15

        client = setup_client()
        if not client:
            generation_results[story_id] = {
                'status': 'error',
                'progress': 0,
                'message': 'Failed to initialize API client',
                'error': 'API key not configured properly'
            }
            return

        # Setup output directory
        generation_results[story_id]['message'] = 'Creating output directory...'
        generation_results[story_id]['progress'] = 20

        project_dir = Path(__file__).parent.parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_dir / "generated_stories" / f"story_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Enhanced story prompt with style and character info
        enhanced_prompt = story_prompt
        if character_name:
            enhanced_prompt = f"A story about {character_name}: {story_prompt}"
        if setting:
            enhanced_prompt += f" The story takes place in {setting}."
        enhanced_prompt += f" Create this in {style} art style."

        generation_results[story_id]['message'] = 'Starting AI story generation...'
        generation_results[story_id]['progress'] = 25

        # Use the imported generation function with progress callback
        def progress_callback(scene_num, total, message):
            # Calculate progress: 25% for setup, 70% for generation, 5% for finishing
            generation_progress = 25 + (scene_num / total) * 70
            generation_results[story_id]['progress'] = int(generation_progress)
            generation_results[story_id]['message'] = message
            generation_results[story_id]['current_scene'] = scene_num
            if scene_num > 0:
                generation_results[story_id]['scenes_completed'].append(scene_num)

        # Generate story with images
        story_data = generate_custom_story_with_images(
            client, enhanced_prompt, num_scenes, output_dir
        )

        if not story_data:
            generation_results[story_id] = {
                'status': 'error',
                'progress': 0,
                'message': 'Story generation failed',
                'error': 'Failed to generate story content. Check your API quota.'
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

        generation_results[story_id]['progress'] = 95
        generation_results[story_id]['message'] = 'Creating HTML and PDF versions...'

        # Create HTML display
        html_path = create_html_display(story_data, output_dir)
        story_data['html_path'] = html_path

        # Create PDF version
        pdf_path = create_pdf_from_html(html_path, output_dir)
        if pdf_path:
            story_data['pdf_path'] = pdf_path

        # Save story metadata
        metadata_path = output_dir / "story_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, indent=2, ensure_ascii=False)

        generation_results[story_id] = {
            'status': 'complete',
            'progress': 100,
            'message': f'Story generation complete! Created {num_scenes} scenes.',
            'data': story_data,
            'current_scene': num_scenes,
            'total_scenes': num_scenes
        }

    except Exception as e:
        generation_results[story_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Error: {e!s}',
            'error': str(e)
        }


@app.route('/')
def index():
    """Main page with modern interface."""
    api_key_configured = bool(os.getenv('GOOGLE_API_KEY'))
    return render_template('index.html', api_key_configured=api_key_configured)


@app.route('/generate', methods=['POST'])
def generate_story():
    """Start unlimited story generation."""
    if not os.getenv('GOOGLE_API_KEY'):
        return jsonify({'error': 'API key not configured'}), 400

    data = request.json
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    story_prompt = data.get('story_prompt', '').strip()
    num_scenes = int(data.get('num_scenes', 6))
    character_name = data.get('character_name', '').strip()
    setting = data.get('setting', '').strip()
    style = data.get('style', 'cartoon').strip()

    if not story_prompt:
        return jsonify({'error': 'Story prompt is required'}), 400

    # NO ARTIFICIAL LIMITS! User decides how many scenes they want
    num_scenes = max(num_scenes, 1)

    # Generate unique story ID
    story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    # Start background generation
    thread = threading.Thread(
        target=generate_story_background,
        args=(story_id, story_prompt, num_scenes, character_name, setting, style)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'story_id': story_id,
        'num_scenes': num_scenes,
        'estimated_minutes': num_scenes * 6 / 60
    })


@app.route('/status/<story_id>')
def get_status(story_id):
    """Get detailed generation status."""
    if story_id in generation_results:
        return jsonify(generation_results[story_id])
    else:
        return jsonify({'status': 'not_found'}), 404


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve generated images."""
    project_dir = Path(__file__).parent.parent
    stories_dir = project_dir / "generated_stories"
    for story_dir in stories_dir.glob("story_*"):
        image_path = story_dir / filename
        if image_path.exists():
            return send_from_directory(str(story_dir), filename)
    return "Image not found", 404


@app.route('/download/<story_id>/<format>')
def download_story(story_id, format):
    """Download story in specified format."""
    if story_id not in generation_results or generation_results[story_id]['status'] != 'complete':
        return "Story not ready", 400

    story_data = generation_results[story_id]['data']
    safe_name = "".join(c for c in story_data.get('original_prompt', 'story')[:30] if c.isalnum() or c in (' ', '-', '_')).strip()

    if format == 'html' and 'html_path' in story_data:
        html_path = Path(story_data['html_path'])
        if html_path.exists():
            return send_file(html_path, as_attachment=True, download_name=f"{safe_name}.html")

    elif format == 'pdf' and 'pdf_path' in story_data:
        pdf_path = Path(story_data['pdf_path'])
        if pdf_path.exists():
            return send_file(pdf_path, as_attachment=True, download_name=f"{safe_name}.pdf")

    return "File not found", 404


@app.route('/gallery')
def gallery():
    """Enhanced gallery with better sorting and display."""
    project_dir = Path(__file__).parent.parent
    stories_dir = project_dir / "generated_stories"
    stories = []

    if stories_dir.exists():
        for story_dir in sorted(stories_dir.glob("story_*"), reverse=True):
            metadata_file = story_dir / "story_metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, encoding='utf-8') as f:
                        metadata = json.load(f)

                    # Find files
                    html_files = list(story_dir.glob("*.html"))
                    pdf_files = list(story_dir.glob("*.pdf"))
                    image_files = list(story_dir.glob("scene_*.png"))

                    if html_files:
                        metadata['html_file'] = html_files[0].name
                    if pdf_files:
                        metadata['pdf_file'] = pdf_files[0].name

                    metadata['folder'] = story_dir.name
                    metadata['image_count'] = len(image_files)
                    metadata['file_size'] = sum(f.stat().st_size for f in story_dir.iterdir()) / 1024 / 1024  # MB

                    stories.append(metadata)
                except Exception:
                    continue

    return render_template('gallery.html', stories=stories)


@app.route('/generated_stories/<path:filename>')
def serve_generated_file(filename):
    """Serve files from generated_stories directory."""
    project_dir = Path(__file__).parent.parent
    stories_dir = project_dir / "generated_stories"
    return send_from_directory(str(stories_dir), filename)


def create_templates_if_needed():
    """Create HTML templates if they don't exist."""
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)

    # Only create templates if they don't exist
    index_template_path = templates_dir / "index.html"
    gallery_template_path = templates_dir / "gallery.html"

    if not index_template_path.exists():
        # Modern, responsive index template with unlimited scenes
        index_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Story Generator - Unlimited Scenes</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.3);
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.2rem;
            color: #666;
            font-weight: 300;
        }

        .nav {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
        }

        .nav a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nav a:hover {
            background: rgba(102, 126, 234, 0.1);
            transform: translateY(-2px);
        }

        .form-container {
            display: grid;
            gap: 25px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        .form-group label {
            font-weight: 600;
            color: #444;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: white;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-group textarea {
            min-height: 120px;
            resize: vertical;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
        }

        .scene-input-container {
            position: relative;
        }

        .scene-input {
            width: 100%;
        }

        .scene-presets {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }

        .preset-btn {
            background: #f8f9fa;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #666;
        }

        .preset-btn:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }

        .generate-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px 40px;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 30px auto;
            display: block;
            min-width: 200px;
        }

        .generate-btn:hover:not(:disabled) {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        .generate-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .progress-container {
            display: none;
            margin: 30px 0;
            text-align: center;
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .progress-text {
            font-weight: 500;
            color: #444;
        }

        .progress-stats {
            font-size: 14px;
            color: #666;
        }

        .progress-bar {
            width: 100%;
            height: 12px;
            background: #f0f0f0;
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 15px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.5s ease;
            border-radius: 6px;
        }

        .story-container {
            display: none;
            margin-top: 40px;
        }

        .story-header {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 30px;
        }

        .story-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .story-meta {
            opacity: 0.9;
            font-size: 1.1rem;
        }

        .download-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }

        .download-btn {
            background: #28a745;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            margin: 8px;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .download-btn:hover {
            background: #218838;
            transform: translateY(-2px);
        }

        .scene {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin: 25px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }

        .scene-number {
            color: #667eea;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .scene img {
            width: 100%;
            max-width: 600px;
            height: auto;
            border-radius: 12px;
            margin: 20px auto;
            display: block;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }

        .scene-text {
            font-size: 1.1rem;
            line-height: 1.8;
            color: #555;
            margin: 15px 0;
        }

        .alert {
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }

        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .estimation-info {
            background: #e3f2fd;
            color: #1976d2;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            font-size: 14px;
            border-left: 4px solid #1976d2;
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }

            .glass-card {
                padding: 25px;
            }

            .header h1 {
                font-size: 2rem;
            }

            .nav {
                flex-direction: column;
                gap: 15px;
            }

            .form-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="glass-card">
            <div class="header">
                <h1><i class="fas fa-magic"></i> AI Story Generator</h1>
                <p>Create unlimited epic adventures with AI-generated images</p>
            </div>

            <div class="nav">
                <a href="/"><i class="fas fa-home"></i> Generator</a>
                <a href="/gallery"><i class="fas fa-images"></i> Gallery</a>
            </div>

            {% if not api_key_configured %}
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                    <strong>API Key Required</strong><br>
                    Please configure your Google API key in the .env file to use this application.
                </div>
            </div>
            {% else %}

            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                <div>
                    <strong>Unlimited Scenes!</strong> Create stories with as many scenes as you want.
                    API limits: 10 requests/minute (~6 seconds per scene).
                </div>
            </div>

            <form id="storyForm" class="form-container">
                <div class="form-group">
                    <label for="story_prompt"><i class="fas fa-lightbulb"></i> What's your story idea? *</label>
                    <textarea id="story_prompt" name="story_prompt"
                              placeholder="Describe your epic adventure... A brave dragon who's afraid of heights, a robot that dreams of becoming a chef, a magical library where stories come alive..."
                              required></textarea>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="character_name"><i class="fas fa-user"></i> Main character name</label>
                        <input type="text" id="character_name" name="character_name"
                               placeholder="e.g., Luna, Max, Zara, Captain Stardust...">
                    </div>
                    <div class="form-group">
                        <label for="setting"><i class="fas fa-map-marker-alt"></i> Story setting</label>
                        <input type="text" id="setting" name="setting"
                               placeholder="e.g., enchanted forest, space station, underwater city...">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="style"><i class="fas fa-palette"></i> Art style</label>
                        <select id="style" name="style">
                            <option value="cartoon">🎨 Cartoon</option>
                            <option value="anime">🇯🇵 Anime</option>
                            <option value="realistic">📸 Realistic</option>
                            <option value="watercolor">🎨 Watercolor</option>
                            <option value="digital art">💻 Digital Art</option>
                            <option value="oil painting">🖼️ Oil Painting</option>
                            <option value="sketch">✏️ Sketch</option>
                            <option value="fantasy art">⚔️ Fantasy Art</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="num_scenes"><i class="fas fa-list-ol"></i> Number of scenes</label>
                        <div class="scene-input-container">
                            <input type="number" id="num_scenes" name="num_scenes" value="6" min="1" max="9999" class="scene-input">
                            <div class="scene-presets">
                                <button type="button" class="preset-btn" onclick="setScenes(3)">3 Quick</button>
                                <button type="button" class="preset-btn" onclick="setScenes(6)">6 Standard</button>
                                <button type="button" class="preset-btn" onclick="setScenes(12)">12 Long</button>
                                <button type="button" class="preset-btn" onclick="setScenes(25)">25 Epic</button>
                                <button type="button" class="preset-btn" onclick="setScenes(50)">50 Novel</button>
                                <button type="button" class="preset-btn" onclick="setScenes(100)">100 Saga</button>
                            </div>
                        </div>
                        <div id="estimationInfo" class="estimation-info">
                            <i class="fas fa-clock"></i> Estimated time: ~0.6 minutes (6 scenes)
                        </div>
                    </div>
                </div>

                <button type="submit" class="generate-btn" id="generateBtn">
                    <i class="fas fa-rocket"></i> Generate Story
                </button>
            </form>

            <div class="progress-container" id="progressContainer">
                <div class="progress-header">
                    <div class="progress-text" id="progressText">Preparing...</div>
                    <div class="progress-stats" id="progressStats">0%</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div id="detailedProgress" style="font-size: 14px; color: #666; margin-top: 10px;"></div>
            </div>

            <div class="story-container" id="storyContainer">
                <!-- Story content will be inserted here -->
            </div>

            {% endif %}
        </div>
    </div>

    <script>
        let currentStoryId = null;
        let pollInterval = null;

        // Update estimation when scene count changes
        document.getElementById('num_scenes').addEventListener('input', updateEstimation);

        function setScenes(count) {
            document.getElementById('num_scenes').value = count;
            updateEstimation();
        }

        function updateEstimation() {
            const scenes = parseInt(document.getElementById('num_scenes').value) || 6;
            const minutes = scenes * 6 / 60;
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = Math.floor(minutes % 60);

            let timeStr;
            if (hours > 0) {
                timeStr = `~${hours}h ${remainingMinutes}m`;
            } else {
                timeStr = `~${minutes.toFixed(1)} minutes`;
            }

            document.getElementById('estimationInfo').innerHTML =
                `<i class="fas fa-clock"></i> Estimated time: ${timeStr} (${scenes} scenes)`;
        }

        document.getElementById('storyForm').addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(e.target);
            const data = {
                story_prompt: formData.get('story_prompt'),
                character_name: formData.get('character_name'),
                setting: formData.get('setting'),
                style: formData.get('style'),
                num_scenes: parseInt(formData.get('num_scenes'))
            };

            // Validate
            if (!data.story_prompt.trim()) {
                alert('Please enter a story idea');
                return;
            }

            if (data.num_scenes < 1) {
                alert('Please enter at least 1 scene');
                return;
            }

            // Confirmation for large stories
            if (data.num_scenes > 50) {
                const confirm = window.confirm(
                    `You're about to create a ${data.num_scenes}-scene story! \\n` +
                    `This will take approximately ${(data.num_scenes * 6 / 60).toFixed(1)} minutes. \\n` +
                    `Are you sure you want to continue?`
                );
                if (!confirm) return;
            }

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
            document.getElementById('generateBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('storyContainer').style.display = 'none';
        }

        function hideProgress() {
            document.getElementById('generateBtn').disabled = false;
            document.getElementById('generateBtn').innerHTML = '<i class="fas fa-rocket"></i> Generate Story';
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
            }, 2000);
        }

        function updateProgress(status) {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            const progressStats = document.getElementById('progressStats');
            const detailedProgress = document.getElementById('detailedProgress');

            progressFill.style.width = status.progress + '%';
            progressText.textContent = status.message || 'Processing...';
            progressStats.textContent = status.progress + '%';

            if (status.current_scene && status.total_scenes) {
                detailedProgress.innerHTML =
                    `<i class="fas fa-images"></i> Scene ${status.current_scene} of ${status.total_scenes} completed`;
            }
        }

        function displayStory(storyData) {
            const container = document.getElementById('storyContainer');
            container.innerHTML = '';

            // Story header
            const header = document.createElement('div');
            header.className = 'story-header';
            header.innerHTML = `
                <div class="story-title">${storyData.original_prompt}</div>
                <div class="story-meta">
                    <i class="fas fa-user"></i> ${storyData.character_name || 'Auto-chosen'} |
                    <i class="fas fa-map-marker-alt"></i> ${storyData.setting || 'Auto-chosen'} |
                    <i class="fas fa-palette"></i> ${storyData.style} style |
                    <i class="fas fa-images"></i> ${storyData.num_scenes} scenes
                </div>
            `;
            container.appendChild(header);

            // Download section
            const downloadSection = document.createElement('div');
            downloadSection.className = 'download-section';
            downloadSection.innerHTML = `
                <h3><i class="fas fa-download"></i> Download Your Story</h3>
                <a href="/download/${currentStoryId}/html" class="download-btn">
                    <i class="fas fa-file-code"></i> Download HTML
                </a>
                <a href="/download/${currentStoryId}/pdf" class="download-btn">
                    <i class="fas fa-file-pdf"></i> Download PDF
                </a>
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

                let sceneHTML = `<div class="scene-number"><i class="fas fa-play-circle"></i> Scene ${sceneNum}</div>`;

                // Add image
                if (imageScenes[sceneNum]) {
                    sceneHTML += `<img src="/images/${imageScenes[sceneNum].filename}" alt="Scene ${sceneNum}" loading="lazy">`;
                }

                // Add text
                if (textScenes[sceneNum]) {
                    textScenes[sceneNum].forEach(text => {
                        sceneHTML += `<div class="scene-text">${text.replace(/\\n/g, '<br>')}</div>`;
                    });
                }

                sceneDiv.innerHTML = sceneHTML;
                container.appendChild(sceneDiv);
            });

            container.style.display = 'block';

            // Scroll to story
            container.scrollIntoView({ behavior: 'smooth' });
        }

        function showError(message) {
            const container = document.getElementById('storyContainer');
            container.innerHTML = `
                <div class="alert alert-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <div><strong>Error:</strong> ${message}</div>
                </div>
            `;
            container.style.display = 'block';
        }

        // Initialize
        updateEstimation();
    </script>
</body>
</html>
        """

        with open(index_template_path, 'w', encoding='utf-8') as f:
            f.write(index_template)

    if not gallery_template_path.exists():
        # Enhanced gallery template
        gallery_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Story Gallery - AI Story Generator</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.3);
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        .nav {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
        }

        .nav a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nav a:hover {
            background: rgba(102, 126, 234, 0.1);
            transform: translateY(-2px);
        }

        .story-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
        }

        .story-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .story-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }

        .story-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
            font-size: 1.1rem;
            line-height: 1.4;
        }

        .story-meta {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 20px;
            display: grid;
            gap: 8px;
        }

        .meta-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .story-stats {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            text-align: center;
        }

        .stat {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }

        .stat-value {
            font-weight: 600;
            color: #667eea;
        }

        .stat-label {
            font-size: 0.8rem;
            color: #666;
        }

        .story-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        .story-actions a {
            background: #667eea;
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.3s ease;
            flex: 1;
            justify-content: center;
        }

        .story-actions a:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }

        .story-actions a.pdf {
            background: #dc3545;
        }

        .story-actions a.pdf:hover {
            background: #c82333;
        }

        .no-stories {
            text-align: center;
            color: #666;
            margin: 80px 0;
        }

        .no-stories h3 {
            font-size: 1.5rem;
            margin-bottom: 15px;
            color: #444;
        }

        .no-stories a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            padding: 12px 25px;
            border: 2px solid #667eea;
            border-radius: 10px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 20px;
            transition: all 0.3s ease;
        }

        .no-stories a:hover {
            background: #667eea;
            color: white;
        }

        .gallery-stats {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
            color: #1976d2;
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }

            .glass-card {
                padding: 25px;
            }

            .header h1 {
                font-size: 2rem;
            }

            .story-grid {
                grid-template-columns: 1fr;
            }

            .nav {
                flex-direction: column;
                gap: 15px;
            }

            .story-stats {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="glass-card">
            <div class="header">
                <h1><i class="fas fa-images"></i> Story Gallery</h1>
                <p>Your AI-generated adventures</p>
            </div>

            <div class="nav">
                <a href="/"><i class="fas fa-home"></i> Generator</a>
                <a href="/gallery"><i class="fas fa-images"></i> Gallery</a>
            </div>

            {% if stories %}
                <div class="gallery-stats">
                    <i class="fas fa-chart-bar"></i>
                    <strong>{{ stories|length }}</strong> stories created |
                    <strong>{{ stories|sum(attribute='num_scenes') }}</strong> total scenes |
                    <strong>{{ "%.1f"|format(stories|sum(attribute='file_size')) }}</strong> MB total
                </div>

                <div class="story-grid">
                    {% for story in stories %}
                    <div class="story-card">
                        <div class="story-title">{{ story.original_prompt }}</div>

                        <div class="story-meta">
                            <div class="meta-item">
                                <i class="fas fa-user"></i>
                                {{ story.character_name or 'Auto-chosen character' }}
                            </div>
                            <div class="meta-item">
                                <i class="fas fa-palette"></i>
                                {{ story.style or 'cartoon' }} style
                            </div>
                            <div class="meta-item">
                                <i class="fas fa-calendar"></i>
                                {{ story.generated_at[:19].replace('T', ' ') }}
                            </div>
                        </div>

                        <div class="story-stats">
                            <div class="stat">
                                <div class="stat-value">{{ story.num_scenes }}</div>
                                <div class="stat-label">Scenes</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ story.image_count or 0 }}</div>
                                <div class="stat-label">Images</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ "%.1f"|format(story.file_size or 0) }} MB</div>
                                <div class="stat-label">Size</div>
                            </div>
                        </div>

                        <div class="story-actions">
                            {% if story.html_file %}
                            <a href="/generated_stories/{{ story.folder }}/{{ story.html_file }}" target="_blank">
                                <i class="fas fa-eye"></i> View
                            </a>
                            {% endif %}
                            {% if story.pdf_file %}
                            <a href="/generated_stories/{{ story.folder }}/{{ story.pdf_file }}" target="_blank" class="pdf">
                                <i class="fas fa-file-pdf"></i> PDF
                            </a>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="no-stories">
                    <h3>No stories generated yet</h3>
                    <p>Create your first AI story to see it here!</p>
                    <a href="/">
                        <i class="fas fa-rocket"></i> Generate Story
                    </a>
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
        """

        with open(gallery_template_path, 'w', encoding='utf-8') as f:
            f.write(gallery_template)


def main():
    """Main entry point for the Flask web UI."""
    print("🚀 Starting Modern AI Story Generator UI v2.1")
    print("✨ Features: UNLIMITED scenes, modern design, real-time progress")
    print("🌐 Open your browser to: http://localhost:8080")
    print("📱 Mobile-friendly responsive design")
    print("🎯 No scene limitations - create epic 1000+ scene sagas!")

    # Create templates if needed
    create_templates_if_needed()

    app.run(host='0.0.0.0', port=8080, debug=False)


if __name__ == '__main__':
    main()
