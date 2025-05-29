#!/usr/bin/env python3
"""
Batch PDF Regenerator for AI Story Generator

This script helps regenerate PDFs for existing stories with enhanced formatting.

Usage:
    python3 regenerate_pdfs.py                    # Process all stories
    python3 regenerate_pdfs.py <story_directory>  # Process specific story

Author: Assistant
Date: 2025-05-28
"""

import sys
import json
from pathlib import Path
from enhanced_pdf_generator import regenerate_existing_story_pdf


def find_all_stories():
    """Find all story directories."""
    project_dir = Path(__file__).parent
    stories_dir = project_dir / "generated_stories"
    
    if not stories_dir.exists():
        print("❌ No generated_stories directory found")
        return []
    
    story_dirs = []
    for story_dir in stories_dir.glob("story_*"):
        if story_dir.is_dir():
            story_dirs.append(story_dir)
    
    return sorted(story_dirs)


def get_story_info(story_dir):
    """Get basic info about a story."""
    metadata_file = story_dir / "story_metadata.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            return {
                'title': data.get('original_prompt', 'Unknown')[:50],
                'scenes': data.get('num_scenes', 'Unknown'),
                'generated': data.get('generated_at', 'Unknown')[:19].replace('T', ' ')
            }
        except:
            pass
    
    # Fallback info
    scene_count = len(list(story_dir.glob("scene_*.png")))
    return {
        'title': story_dir.name.replace('story_', '').replace('_', ' '),
        'scenes': scene_count,
        'generated': 'Unknown'
    }


def regenerate_all_stories():
    """Regenerate PDFs for all existing stories."""
    story_dirs = find_all_stories()
    
    if not story_dirs:
        print("📭 No stories found to regenerate")
        return
    
    print(f"🔍 Found {len(story_dirs)} stories to process")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, story_dir in enumerate(story_dirs, 1):
        story_info = get_story_info(story_dir)
        print(f"\n📖 [{i}/{len(story_dirs)}] Processing: {story_info['title']}")
        print(f"   📊 Scenes: {story_info['scenes']} | Generated: {story_info['generated']}")
        
        try:
            result = regenerate_existing_story_pdf(str(story_dir))
            if result:
                print(f"   ✅ Enhanced PDF created: {Path(result).name}")
                successful += 1
            else:
                print(f"   ❌ PDF generation failed")
                failed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📈 Summary: {successful} successful, {failed} failed")
    if successful > 0:
        print("🎉 Enhanced PDFs are ready with better page formatting!")


def regenerate_single_story(story_path):
    """Regenerate PDF for a single story."""
    story_dir = Path(story_path)
    
    if not story_dir.exists():
        print(f"❌ Story directory not found: {story_path}")
        return False
    
    story_info = get_story_info(story_dir)
    print(f"📖 Processing: {story_info['title']}")
    print(f"📊 Scenes: {story_info['scenes']} | Generated: {story_info['generated']}")
    
    try:
        result = regenerate_existing_story_pdf(str(story_dir))
        if result:
            print(f"✅ Enhanced PDF created: {Path(result).name}")
            return True
        else:
            print("❌ PDF generation failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main function."""
    print("🔧 PDF Regenerator for AI Story Generator")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Process specific story
        story_path = sys.argv[1]
        print(f"🎯 Processing specific story: {story_path}")
        success = regenerate_single_story(story_path)
        if success:
            print("\n🎉 Done! Your enhanced PDF is ready with proper page breaks.")
        else:
            print("\n😞 PDF generation failed. Check the error messages above.")
    else:
        # Process all stories
        print("🔄 Processing all existing stories...")
        regenerate_all_stories()
    
    print("\n💡 Enhanced PDFs have:")
    print("   📄 Each scene on its own page")
    print("   📖 Print-optimized typography")
    print("   🎨 Proper image sizing for print")
    print("   📑 Table of contents (for longer stories)")


if __name__ == "__main__":
    main()
