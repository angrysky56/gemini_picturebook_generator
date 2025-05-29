#!/usr/bin/env python3
"""
Simple HTML inspector to see what's actually in the file
"""

from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path("/home/ty/Repositories/ai_workspace/gemini_picturebook_generator/generated_stories/story_20250528_165909/The_story_of_the_first_embodie_story.html")

print("📖 Reading HTML file...")
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

print(f"📊 HTML file size: {len(html_content)} characters")

# Look for the first scene to see its structure
first_scene_start = html_content.find('<div class="scene">')
if first_scene_start != -1:
    # Get the first 1000 characters of the first scene
    first_scene_end = html_content.find('</div>', first_scene_start + 1000)
    if first_scene_end == -1:
        first_scene_end = first_scene_start + 1000

    scene_html = html_content[first_scene_start:first_scene_end + 6]
    print("\n🎬 First scene HTML structure:")
    print(scene_html)

    # Now parse with BeautifulSoup and see what we get
    print("\n🔍 BeautifulSoup parsing of first scene:")
    soup = BeautifulSoup(scene_html, 'html.parser')
    scene_div = soup.find(class_='scene')
    from bs4.element import Tag, NavigableString
    if scene_div and isinstance(scene_div, Tag):
        print(f"Scene div found: {scene_div.name}")
        all_children = [child for child in scene_div.children if isinstance(child, (Tag, NavigableString))]
        print(f"Children count: {len(all_children)}")
        for i, child in enumerate(all_children):
            if isinstance(child, Tag):
                child_name = child.name
                classes = child.get('class', None)
                print(f"  Child {i}: {child_name} with classes {classes}")
                if child_name == 'div' and classes and 'scene-text' in classes:
                    print(f"    TEXT: {child.get_text()[:100]}...")
            elif isinstance(child, NavigableString) and str(child).strip():
                print(f"  Child {i}: TEXT NODE: '{str(child).strip()[:50]}...'")
    elif scene_div:
        print(f"Scene div found but it is not a Tag (type: {type(scene_div)}).")
else:
    print("❌ No scene divs found in HTML")

# Also check for scene-text specifically
scene_text_count = html_content.count('class="scene-text"')
print(f"\n📝 Found {scene_text_count} occurrences of 'class=\"scene-text\"' in raw HTML")

if scene_text_count > 0:
    # Find the first one
    first_scene_text = html_content.find('class="scene-text"')
    start = max(0, first_scene_text - 100)
    end = min(len(html_content), first_scene_text + 200)
    print("First scene-text context:")
    print(html_content[start:end])
