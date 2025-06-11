# Gemini Picture Book Generator 🎨📚 v2.1.0

An AI-powered story generator that creates **unlimited** custom picture books with illustrations using Google's Gemini AI. Now with **MCP Server support** for Claude Desktop integration!

![Modern UI](image-4.png)

## 🔥 **NEW in v2.1.0 - MCP Edition**

### **🤖 Claude Desktop Integration**
- **Full MCP Server** for seamless Claude Desktop integration
- **Generate stories directly from Claude** using natural language
- **Display stories as artifacts** within Claude conversations
- **Gallery management** through Claude interface
- **Real-time progress tracking** in Claude

### **📦 Modern Package Structure**
- **uv-based project management** (faster, more reliable than pip)
- **Proper Python packaging** with pyproject.toml
- **Type hints throughout** for better development experience
- **Modular architecture** for easy extension

### **🛡️ Enhanced Reliability**
- **Process leak prevention** with proper cleanup patterns
- **Signal handling** for graceful shutdowns
- **Background task management** with asyncio
- **Error handling** with detailed logging

## 🎯 **Core Features (Unchanged)**

### **✨ NO SCENE LIMITATIONS!**
- Create stories with **1 to 9,999+ scenes** - your choice!
- Epic 100+ scene novels? ✅ Possible!
- Quick 3-scene stories? ✅ Also perfect!
- Only limited by your API quota and patience

### **🎨 Modern Web UI**
- **Completely redesigned** responsive interface
- **Real-time progress tracking** with scene-by-scene updates
- **Mobile-friendly** design that works on any device
- **Glass morphism** modern styling

### **🚀 Multiple Access Methods**
1. **Claude Desktop Integration** (NEW!)
2. **Modern Web UI**
3. **Command Line Interface**
4. **Python Package API**

## 🚀 **Quick Start**

### **Option 1: Claude Desktop Integration (Recommended)**

1. **Install the package:**
   ```bash
   cd /home/ty/Repositories/ai_workspace/gemini_picturebook_generator
   uv sync
   ```

2. **Set up your API key:**
   ```bash
   cp .env.template .env
   # Edit .env with your Google API key from https://aistudio.google.com/app/apikey
   ```

3. **Add to Claude Desktop config:**
   - Copy the contents of `example_mcp_config.json`
   - Add to your Claude Desktop configuration
   - Update the path and API key as needed

4. **Use with Claude:**
   ```
   Generate a 6-scene story about a robot chef learning to make pizza
   ```

### **Option 2: Modern Web UI**
```bash
uv run gemini-picturebook
# Open browser to http://localhost:8080
```

### **Option 3: Command Line**
```bash
uv run python -m gemini_picturebook_generator.enhanced_story_generator
```

## 🤖 **Claude Desktop MCP Integration**

### **Available Claude Commands**

**Generate Stories:**
```
Create a story about a brave dragon learning to fly with 8 scenes in watercolor style
```

**Browse Gallery:**
```
Show me my generated stories
```

**Display Stories:**
```
Display story [story_id] as an artifact
```

**Check Status:**
```
Test my Gemini API connection
```

### **MCP Configuration**

Add this to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-picturebook-generator": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/ty/Repositories/ai_workspace/gemini_picturebook_generator",
        "run",
        "gemini-picturebook-mcp"
      ],
      "env": {
        "GOOGLE_API_KEY": "your_actual_api_key_here",
        "MCP_SERVER_MODE": "true"
      }
    }
  }
}
```

### **MCP Tools Available**

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| `generate_story` | Create AI picture books | Generate epic adventures |
| `list_generated_stories` | Browse story gallery | View your creations |
| `display_story_as_artifact` | Show stories in Claude | Display beautiful artifacts |
| `get_story_details` | Get detailed story info | Check metadata |
| `test_gemini_connection` | Verify API setup | Troubleshoot issues |

## 🛠️ **Development Setup**

### **Using uv (Recommended)**
```bash
# Clone/navigate to project
cd /home/ty/Repositories/ai_workspace/gemini_picturebook_generator

# Install
uv sync

# Set up environment
cp .env.template .env
# Edit .env with your API key

# Run MCP server in development
uv run gemini-picturebook-mcp

# Run web UI
uv run gemini-picturebook

# Run tests
uv run pytest

# Format code
uv run ruff format .
uv run ruff check . --fix

# Type checking
uv run mypy .
```

### **Using pip (Legacy)**
```bash
pip install -e .
pip install -r requirements.txt
```

## 📊 **Story Examples & Timing**

| Story Size | Scenes | Est. Time | Perfect For | Claude Command |
|------------|--------|-----------|-------------|----------------|
| **Quick** | 3-6 | 0.3-0.6 min | Testing, bedtime | "Create a 3-scene story about..." |
| **Standard** | 8-15 | 0.8-1.5 min | Picture books | "Generate a 12-scene adventure..." |
| **Long** | 20-30 | 2-3 min | Chapter books | "Make a 25-scene epic about..." |
| **Epic** | 50-100 | 5-10 min | Young novels | "Create a 100-scene saga..." |
| **Unlimited** | 1000+ | Hours | Epic adventures | "Generate a 500-scene chronicle..." |

## 🎨 **Art Styles Available**

| Style | Best For | Claude Usage |
|-------|----------|--------------|
| **cartoon** | Kids' stories | "...in cartoon style" |
| **anime** | Action/fantasy | "...in anime style" |
| **realistic** | Educational | "...in realistic style" |
| **watercolor** | Dreamy tales | "...in watercolor style" |
| **digital art** | Modern stories | "...in digital art style" |
| **oil painting** | Classic feel | "...in oil painting style" |
| **sketch** | Quick concepts | "...in sketch style" |
| **fantasy art** | Epic adventures | "...in fantasy art style" |

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required
GOOGLE_API_KEY=your_api_key

# Optional
MCP_SERVER_MODE=true          # For MCP server usage
FLASK_ENV=production          # Web UI environment
API_DELAY_SECONDS=6           # Rate limiting delay
ENABLE_PDF_GENERATION=true    # PDF export toggle
```

### **API Limits & Usage**
- **Rate**: 10 requests/minute (6 seconds per scene)
- **Daily**: 1,500 requests/day for image generation
- **Practical**: Can create 1,500 scenes per day!

## 🏗️ **Project Structure**

```
gemini_picturebook_generator/
├── gemini_picturebook_generator/     # Main package
│   ├── __init__.py                   # Package initialization
│   ├── mcp_server.py                 # MCP server implementation
│   ├── enhanced_story_generator.py   # Core story generation
│   ├── flask_ui.py                   # Web interface
│   ├── run_ui.py                     # UI entry point
│   └── templates/                    # HTML templates (auto-created)
├── prompts/                          # AI guidance prompts
│   ├── ai_tool_usage_guide.md        # Tool usage for AI
│   └── story_creation_guide.md       # Story creation best practices
├── generated_stories/                # Output directory
├── pyproject.toml                    # Modern Python packaging
├── example_mcp_config.json           # Claude Desktop config
├── .env.template                     # Environment template
├── requirements.txt                  # Legacy pip compatibility
└── README.md                         # This file
```

## 🔄 **Migration from v2.0**

If you have an existing v2.0 installation:

1. **Backup your stories:**
   ```bash
   cp -r generated_stories generated_stories_backup
   ```

2. **Install new version:**
   ```bash
   uv sync
   ```

3. **Copy environment:**
   ```bash
   cp .env.template .env
   # Copy your API key from old .env
   ```

4. **Test MCP integration:**
   ```bash
   uv run gemini-picturebook-mcp
   ```

## 🎯 **Claude Integration Examples**

### **Basic Story Generation**
```
User: Create a story about a shy robot learning to dance
Claude: I'll generate that story for you!

[Uses generate_story tool]
[Displays beautiful artifact with story and images]
```

### **Customized Stories**
```
User: Generate a 12-scene watercolor story about Luna the dragon in an enchanted forest
Claude: Creating your custom story with those specifications...

[Uses generate_story with all parameters]
[Shows progress and final artifact]
```

### **Gallery Browsing**
```
User: Show me my recent stories
Claude: Here are your generated stories:

[Uses list_generated_stories]
[Displays gallery with story previews]

User: Display the dragon story
Claude: [Uses display_story_as_artifact to show full story]
```

## 🛟 **Troubleshooting**

### **MCP Server Issues**
```bash
# Test MCP server directly
uv run gemini-picturebook-mcp

# Check Claude Desktop logs
# Look for connection errors in Claude app
```

### **API Issues**
```bash
# Test API connection
uv run python -c "from gemini_picturebook_generator.enhanced_story_generator import test_api_connection; test_api_connection()"
```

### **Common Fixes**
1. **API Key**: Verify at https://aistudio.google.com/app/apikey
2. **Rate Limits**: Wait if you hit daily quota (1,500 requests)
3. **Dependencies**: Run `uv sync` to update packages
4. **Permissions**: Check file permissions on generated_stories/

## 🎉 **What's New vs Previous Versions**

### **v2.1.0 - MCP Edition**
- ✅ Full Claude Desktop integration via MCP
- ✅ Modern uv-based package management
- ✅ Type hints and better code quality
- ✅ Process leak prevention
- ✅ Async/await patterns
- ✅ Enhanced error handling

### **v2.0 - Unlimited Edition**
- ✅ Unlimited scene support (was limited to 20)
- ✅ Modern web interface
- ✅ Real-time progress tracking
- ✅ Enhanced gallery

### **v1.x - Original**
- ✅ Basic story generation
- ✅ Limited scenes
- ✅ Simple interface

## 🌟 **Contributing**

This project uses modern Python packaging and development tools:

```bash
# Development setup
uv sync --group dev

# Code formatting
uv run ruff format .
uv run ruff check . --fix

# Type checking
uv run mypy .

# Testing
uv run pytest

# Pre-commit hooks
uv run pre-commit install
```

## 📄 **License**

MIT License - Create amazing stories freely!

## 🚀 **Ready to Create!**

Your picture book generator is now **unlimited and Claude-integrated**!

**Quick Start with Claude:**
1. Add MCP config to Claude Desktop
2. Ask Claude: "Create a story about..."
3. Watch your story come to life as an artifact!

**Create epic 1000-scene adventures, test with quick 3-scene stories, or anything in between. The only limits are your imagination and your API quota!** 🎨✨

---

**Happy Storytelling!** 📚🎨🤖
