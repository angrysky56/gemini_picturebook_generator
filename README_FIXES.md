# Gemini Picture Book Generator 🎨📚

An AI-powered story generator that creates custom picture books with illustrations using Google's Gemini AI.

## 🔧 Recent Fixes & Improvements

### Version 2.0 - June 2025

**Major Bug Fixes:**
- ✅ Fixed `'NoneType' object has no attribute 'parts'` error
- ✅ Corrected mixed imports between `google.genai` and `google.generativeai`
- ✅ Rebuilt virtual environment with proper dependencies
- ✅ Added comprehensive error handling and debugging
- ✅ Improved API response validation

**New Features:**
- 🔍 API connection testing before story generation
- 📊 Better progress tracking and feedback
- 💾 Story metadata saving (JSON format)
- 🔧 Enhanced debugging information
- ⚡ Improved rate limiting handling
- 🎯 Better error messages with troubleshooting tips

**UI Improvements:**
- 📱 Enhanced HTML output with debug information
- 🎨 Better visual styling for generated stories
- 📄 Improved PDF generation with page breaks
- 📊 Display of generation statistics

## 🚀 Quick Start

### 1. Setup

```bash
# Navigate to the project directory
cd /home/ty/Repositories/ai_workspace/gemini_picturebook_generator

# Activate virtual environment
source venv/bin/activate

# Verify installation (should show success)
python test_api.py
```

### 2. Generate a Story

```bash
# Run the story generator
python enhanced_story_generator.py
```

### 3. Example Usage

```
🎨 Welcome to the Enhanced Custom Story Generator! 🎨
======================================================================

🔍 Testing API connection...
✅ API connection test successful!

📝 Let's create your custom story!
What story would you like to create?: A boy learns to control his flying in dreams
How many scenes? (3-12 recommended, max 20): 6

⏱️  Estimated generation time: ~0.6 minutes
💡 This is due to API rate limits (10 requests/minute)
Continue? (y/n): y
```

## 📂 Project Structure

```
gemini_picturebook_generator/
├── enhanced_story_generator.py    # Main story generator (FIXED)
├── test_api.py                   # API connection tester (NEW)
├── setup.sh                      # Setup script (NEW)
├── flask_ui.py                   # Web UI (existing)
├── requirements.txt              # Updated dependencies
├── .env                          # API key configuration
├── venv/                         # Virtual environment (rebuilt)
├── generated_stories/            # Output directory
│   └── story_YYYYMMDD_HHMMSS/
│       ├── scene_01.png
│       ├── scene_02.png
│       ├── story_name_story.html
│       ├── story_name_story.pdf
│       └── story_metadata.json  # (NEW)
└── templates/                    # HTML templates
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**1. API Key Issues**
```bash
# Check your API key in .env file
cat .env

# If missing or incorrect, update it:
# GOOGLE_API_KEY=your_actual_api_key_here
```

**2. Virtual Environment Issues**
```bash
# If venv doesn't work, recreate it:
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Rate Limiting**
- The system respects Gemini's 10 requests/minute limit
- Expect ~6 seconds between each scene generation
- For 6 scenes: approximately 36 seconds total

**4. Model Not Available**
- The system uses `gemini-2.0-flash-preview-image-generation`
- If unavailable, try `gemini-2.0-flash-lite` (text only)

## 🎯 Available Models (Free Tier)

Based on your model list:
- `gemini-2.0-flash-lite` - 30 rpm, 1500 req/day ✅ (text only)
- `gemini-2.0-flash-preview-image-generation` - Image generation ✅
- `gemini-2.5-flash-preview-05-20` - 10 rpm, 500 req/day ✅
- `gemma-3-27b-it` - 30 rpm, 14400 req/day ✅

## 🌟 Features

### Story Generation
- **Custom Prompts**: Any story idea you can imagine
- **Variable Scenes**: 1-20 scenes (recommended: 3-12)
- **AI-Generated Images**: Unique illustrations for each scene
- **Multiple Formats**: HTML for viewing, PDF for sharing

### Enhanced Error Handling
- Pre-generation API testing
- Detailed error messages with solutions
- Progress tracking during generation
- Automatic fallback suggestions

### Output Quality
- High-resolution images (PNG format)
- Professional HTML layout with CSS styling
- PDF with proper page breaks
- Metadata for debugging and archival

## 🛠️ Development

### Testing New Features
```bash
# Test API connection only
python test_api.py

# Test story generation with minimal example
python enhanced_story_generator.py
# Enter: "A simple test story"
# Scenes: 2
```

### Customizing the Generator
- Edit prompts in `enhanced_story_generator.py`
- Modify HTML styling in the `create_html_display()` function
- Adjust rate limiting in the main generation loop

## 📝 Recent Changes Log

**2025-06-07 - Version 2.0:**
1. **Fixed Core Bug**: Resolved `'NoneType' object has no attribute 'parts'` error
2. **Improved API Handling**: Better response validation and error handling
3. **Enhanced Debugging**: Added comprehensive logging and progress tracking
4. **Rebuilt Environment**: Clean virtual environment with correct dependencies
5. **Added Testing**: New API test script for troubleshooting
6. **Better Documentation**: This comprehensive README

**Previous Issues (Now Fixed):**
- Mixed imports between different Google AI SDKs
- Inconsistent API configuration
- Poor error handling for API responses
- Broken virtual environment paths

## 🎉 Success Indicators

You'll know the system is working when you see:
```
✅ Successfully connected to Google Gemini API
✅ API connection test successful!
🖼️  Found image data (Scene 1)
✅ Scene 1 image saved: scene_01.png
✅ Generated X scene images
📄 HTML story created: /path/to/story.html
📄 PDF story created: /path/to/story.pdf
🎉 Your custom adventure is ready!
```

## 📞 Support

If you encounter issues:
1. Run `python test_api.py` to verify API connection
2. Check the error messages - they now include specific troubleshooting tips
3. Verify your API key is valid and has sufficient quota
4. Ensure you're using the virtual environment: `source venv/bin/activate`

The system is now robust and ready for creating amazing AI-generated picture books! 🎨✨
