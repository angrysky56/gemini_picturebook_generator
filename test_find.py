#!/usr/bin/env python3
"""
Test BeautifulSoup find method specifically
"""

from pathlib import Path
from bs4 import BeautifulSoup

html_path = Path("/home/ty/Repositories/ai_workspace/gemini_picturebook_generator/generated_stories/story_20250528_165909/The_story_of_the_first_embodie_story.html")

with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Test different ways to find scene-text
scene_divs = soup.find_all(class_='scene')
print(f"📊 Found {len(scene_divs)} scene divs")

first_scene = scene_divs[0]
print("\n🔍 Testing different find methods on first scene:")

# Method 1: class_='scene-text'
text_elem1 = first_scene.find(class_='scene-text')
print(f"Method 1 - find(class_='scene-text'): {text_elem1 is not None}")
if text_elem1:
    print(f"  Text: {text_elem1.get_text()[:50]}...")

# Method 2: attrs={'class': 'scene-text'}
text_elem2 = first_scene.find('div', attrs={'class': 'scene-text'})
print(f"Method 2 - find('div', attrs={{'class': 'scene-text'}}): {text_elem2 is not None}")
if text_elem2:
    print(f"  Text: {text_elem2.get_text()[:50]}...")

# Method 3: find all divs and check classes
all_divs = first_scene.find_all('div')
print(f"Method 3 - All divs in scene: {len(all_divs)}")
for i, div in enumerate(all_divs):
    classes = div.get('class', [])
    print(f"  Div {i}: classes = {classes}")
    if 'scene-text' in classes:
        print(f"    FOUND scene-text! Text: {div.get_text()[:50]}...")

# Method 4: CSS selector
text_elem4 = first_scene.select_one('.scene-text')
print(f"Method 4 - select_one('.scene-text'): {text_elem4 is not None}")
if text_elem4:
    print(f"  Text: {text_elem4.get_text()[:50]}...")
