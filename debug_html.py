#!/usr/bin/env python3
"""
Test script to debug HTML extraction

This script will test the HTML parsing to see what's being extracted.
"""

from pathlib import Path
from bs4 import BeautifulSoup
import sys

def debug_html_extraction(html_file_path):
    """Debug the HTML extraction process."""
    print(f"🔍 Debugging HTML extraction for: {html_file_path}")
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        print(f"✅ HTML parsed successfully")
        
        # Test title extraction
        title_elem = soup.find('h2')
        if title_elem:
            title = title_elem.get_text().strip('"')
            print(f"📖 Title: {title}")
        else:
            print("❌ No title found")
        
        # Test model info extraction
        generated_info = soup.find(class_='generated-info')
        if generated_info:
            print(f"📊 Generated info found:")
            info_text = generated_info.get_text()
            print(f"   Raw text: {repr(info_text)}")
            
            for line in info_text.strip().split('\n'):
                line = line.strip()
                if 'Model:' in line:
                    model = line.replace('Model:', '').strip()
                    print(f"   🤖 Model: {model}")
                elif 'Generated on:' in line:
                    date = line.replace('Generated on:', '').strip()
                    print(f"   📅 Date: {date}")
        else:
            print("❌ No generated info found")
        
        # Test scene extraction
        scene_divs = soup.find_all(class_='scene')
        print(f"🎬 Found {len(scene_divs)} scene divs")
        
        for i, scene_div in enumerate(scene_divs[:3]):  # Just test first 3
            print(f"\n--- Scene {i+1} ---")
            
            # Scene number
            scene_number_elem = scene_div.find(class_='scene-number')
            if scene_number_elem:
                scene_num_text = scene_number_elem.get_text()
                print(f"🔢 Scene number text: {repr(scene_num_text)}")
            
            # Image
            img_elem = scene_div.find('img', class_='scene-image')
            if img_elem and img_elem.get('src'):
                print(f"🖼️  Image: {img_elem['src']}")
            
            # Text
            text_elem = scene_div.find(class_='scene-text')
            if text_elem:
                text_content = text_elem.get_text().strip()
                print(f"📝 Text: {text_content[:100]}...")
            else:
                print("❌ No scene text found")
                # Debug: show what's in the scene div
                print(f"   Scene div classes: {scene_div.get('class')}")
                text_divs = scene_div.find_all('div')
                print(f"   Found {len(text_divs)} divs in scene")
                for div in text_divs:
                    div_classes = div.get('class', [])
                    print(f"   Div classes: {div_classes}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        html_path = Path(sys.argv[1])
    else:
        html_path = Path("/home/ty/Repositories/ai_workspace/gemini_picturebook_generator/generated_stories/story_20250528_165909/The_story_of_the_first_embodie_story.html")
    
    debug_html_extraction(html_path)
