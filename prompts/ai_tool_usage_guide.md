# Gemini Picture Book Generator - AI Tool Usage Guide

## 🎨 Overview
This MCP server provides AI-powered story generation capabilities using Google's Gemini API. Create unlimited picture books with custom scenes, characters, and art styles.

## 🛠️ Available Tools

### `generate_story()`
**Purpose**: Generate a complete AI picture book story with images
**When to use**: User wants to create a new story
**Parameters**:
- `story_prompt` (required): The main story idea
- `num_scenes` (optional, default 6): Number of scenes (1-9999+)
- `character_name` (optional): Main character name
- `setting` (optional): Story location/world
- `style` (optional, default "cartoon"): Art style

**Example Usage**:
```python
# Basic story
await generate_story(
    story_prompt="A robot learning to paint masterpieces"
)

# Customized story
await generate_story(
    story_prompt="A shy dragon discovering friendship",
    num_scenes=12,
    character_name="Spark",
    setting="mountain kingdom", 
    style="fantasy art"
)
```

**Best Practices**:
- Use descriptive, engaging prompts
- Start with 3-6 scenes for testing
- Be patient with large stories (rate limiting)
- Include emotions and character development

### `list_generated_stories()`
**Purpose**: Show all generated stories in gallery
**When to use**: User wants to see what stories exist
**Parameters**:
- `limit` (optional, default 20): Max stories to return

**Example Usage**:
```python
# List recent stories
stories = await list_generated_stories(limit=10)
```

### `get_story_details()`
**Purpose**: Get complete information about a specific story
**When to use**: User wants details about a particular story
**Parameters**:
- `story_id` (required): The story identifier

**Example Usage**:
```python
details = await get_story_details("story_20250607_143022_123456")
```

### `display_story_as_artifact()`
**Purpose**: Create an HTML artifact showing the story with images
**When to use**: User wants to view/display a generated story
**Parameters**:
- `story_id` (required): The story to display

**Example Usage**:
```python
# Show a story in an artifact
await display_story_as_artifact("story_20250607_143022_123456")
```

**This is the primary way to show stories to users!**

### `get_generation_status()`
**Purpose**: Check status of ongoing story generation
**When to use**: User asks about generation progress
**Parameters**:
- `story_id` (required): The story being generated

### `test_gemini_connection()`
**Purpose**: Test API connection and configuration
**When to use**: Troubleshooting connection issues

## 🎯 Common Workflows

### 1. Create and Display Story
```python
# Generate story
result = await generate_story(
    story_prompt="A cat superhero saving the city",
    num_scenes=6,
    character_name="Captain Whiskers",
    style="cartoon"
)

# Parse result and display
story_data = json.loads(result)
if story_data["success"]:
    await display_story_as_artifact(story_data["story_id"])
```

### 2. Browse Existing Stories
```python
# List stories
stories_result = await list_generated_stories(limit=10)
stories_data = json.loads(stories_result)

# Show a specific story
if stories_data["stories"]:
    story_id = stories_data["stories"][0]["id"]
    await display_story_as_artifact(story_id)
```

### 3. Troubleshoot Issues
```python
# Test connection
connection_result = await test_gemini_connection()
print(json.loads(connection_result))
```

## 🎨 Art Style Guide

| Style | Best For | Description |
|-------|----------|-------------|
| `cartoon` | Children's stories | Fun, colorful, kid-friendly |
| `anime` | Adventure/action | Japanese animation style |
| `realistic` | Educational content | Photographic quality |
| `watercolor` | Gentle stories | Soft, artistic painting |
| `digital art` | Modern themes | Contemporary digital illustration |
| `oil painting` | Classic tales | Traditional painted style |
| `sketch` | Rough concepts | Hand-drawn pencil style |
| `fantasy art` | Epic adventures | Magical, mythical themes |

## ⏱️ Timing Expectations

| Scenes | Estimated Time | Best For |
|--------|---------------|----------|
| 3-6 | 18-36 seconds | Quick stories, testing |
| 8-15 | 48-90 seconds | Standard picture books |
| 20-30 | 2-3 minutes | Chapter books |
| 50+ | 5+ minutes | Novels, epics |

**Important**: Generation uses 6-second rate limiting per scene due to API limits.

## 🚨 Error Handling

### Common Errors and Solutions:

1. **API Key Issues**
   - Error: "API key not configured"
   - Solution: Set GOOGLE_API_KEY environment variable
   - Get key: https://aistudio.google.com/app/apikey

2. **Quota Exceeded**
   - Error: "quota" or "rate" in error message
   - Solution: Wait 24 hours or upgrade plan
   - Free tier: 1,500 requests/day

3. **Generation Failed**
   - Error: "Story generation failed"
   - Solution: Check prompt length, API quota, network

4. **Story Not Found**
   - Error: "Story {id} not found"
   - Solution: Use `list_generated_stories()` to find valid IDs

## 💡 AI Assistant Guidelines

### When User Asks for Stories:
1. **Always use `generate_story()` first** to create the story
2. **Immediately follow with `display_story_as_artifact()`** to show it
3. **Parse JSON responses** to check for success/errors
4. **Provide helpful guidance** on scene counts and timing

### For Story Browsing:
1. **Use `list_generated_stories()`** to show available stories
2. **Let user pick which to view** 
3. **Use `display_story_as_artifact()`** to show selected stories

### For Troubleshooting:
1. **Use `test_gemini_connection()`** first
2. **Check error messages** in JSON responses
3. **Guide users to proper API setup** if needed

### Best Practices:
- **Always display stories as artifacts** after generation
- **Explain timing expectations** for large stories
- **Suggest starting small** for new users (3-6 scenes)
- **Be patient with rate limiting** - it's normal!
- **Parse and handle JSON responses** properly

## 🎉 Example User Interactions

### User: "Create a story about a robot chef"
```python
result = await generate_story(
    story_prompt="A robot who dreams of becoming a master chef and opens a restaurant",
    num_scenes=8,
    character_name="Chef Bot",
    setting="futuristic kitchen",
    style="digital art"
)

story_data = json.loads(result)
if story_data["success"]:
    await display_story_as_artifact(story_data["story_id"])
else:
    # Handle error appropriately
```

### User: "Show me my stories"
```python
stories_result = await list_generated_stories()
stories_data = json.loads(stories_result)

if stories_data["success"] and stories_data["stories"]:
    # Present list and let user choose
    # Then display chosen story with display_story_as_artifact()
```

### User: "My story generation isn't working"
```python
connection_result = await test_gemini_connection()
# Guide user based on test results
```

## 🎯 Success Metrics
- **High-quality prompts** lead to better stories
- **Appropriate scene counts** for story type
- **Successful artifact display** for user viewing
- **Proper error handling** for smooth experience

Remember: The goal is to create engaging, visual stories that users can immediately view and enjoy!
