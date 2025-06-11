# 🚀 Quick Start Guide

## Immediate Setup (5 minutes)

### 1. Verify Installation
```bash
cd /home/ty/Repositories/ai_workspace/gemini_picturebook_generator
uv run python test_installation.py
```

### 2. Configure API Key
```bash
# Copy template and edit
cp .env.template .env
# Edit .env with your Google API key from https://aistudio.google.com/app/apikey
```

### 3. Test MCP Server
```bash
# Test server starts correctly
uv run gemini-picturebook-mcp
# Press Ctrl+C to stop
```

### 4. Add to Claude Desktop
Copy this to your Claude Desktop config (`~/.claude/claude_desktop_config.json`):

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

### 5. Start Using with Claude!

**First Story:**
```
Generate a 3-scene cartoon story about a robot learning to bake cookies
```

**Custom Story:**
```
Create a 12-scene watercolor story about Luna the dragon who's afraid of heights, set in a mountain kingdom
```

**Browse Gallery:**
```
Show me my generated stories
```

**Display Story:**
```
Display story [story_id] as an artifact
```

## Alternative: Web Interface

```bash
uv run gemini-picturebook
# Open http://localhost:8080
```

## ✅ Success Indicators

- ✅ Test script passes all checks
- ✅ MCP server starts without errors  
- ✅ Claude Desktop shows the server as connected
- ✅ You can generate stories through Claude

## 🛟 Quick Troubleshooting

**"API key not configured"**: Edit `.env` file with real API key
**"Connection failed"**: Verify API key at https://aistudio.google.com/app/apikey  
**"Server not found"**: Check path in Claude Desktop config
**"Permission denied"**: Run `chmod +x` on the project directory

## 📚 First Story Ideas

- "A shy robot learning to paint masterpieces"
- "A young scientist discovering time travel"  
- "A cat superhero saving the neighborhood"
- "A dragon who's afraid of flying"
- "A magical library where books come alive"

**Happy storytelling!** 🎨📚✨
