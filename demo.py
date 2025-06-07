#!/usr/bin/env python3
"""
Quick demo script to test the fixed picture book generator.
This runs a minimal example to verify everything is working.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import our fixed modules
from enhanced_story_generator import setup_client, generate_custom_story_with_images, create_html_display, test_api_connection
from datetime import datetime

def quick_demo():
    """Run a quick demo to test the system."""
    print("🎯 Quick Demo: Testing Fixed Picture Book Generator")
    print("=" * 60)
    
    # Test API connection first
    print("\n🔍 Step 1: Testing API connection...")
    if not test_api_connection():
        print("❌ API test failed. Please check your setup.")
        return False
    
    # Setup output directory
    project_dir = Path(__file__).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_dir / "generated_stories" / f"demo_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Step 2: Output directory created: {output_dir}")
    
    # Initialize client
    print("\n🔧 Step 3: Initializing Gemini client...")
    try:
        client = setup_client()
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Generate a simple 2-scene story
    print("\n🎨 Step 4: Generating demo story (2 scenes)...")
    story_prompt = "A friendly robot discovers a beautiful garden and learns about flowers"
    num_scenes = 2
    
    story_data = generate_custom_story_with_images(
        client=client,
        story_prompt=story_prompt,
        num_scenes=num_scenes,
        output_dir=output_dir,
        delay_between_requests=3  # Shorter delay for demo
    )
    
    if story_data:
        print("\n✅ Step 5: Story generation successful!")
        
        # Create HTML display
        html_path = create_html_display(story_data, output_dir)
        print(f"📄 HTML created: {html_path}")
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"📂 Files saved in: {output_dir}")
        print(f"💻 Open {html_path} in your browser to view the story")
        
        # Show summary
        print(f"\n📊 Generation Summary:")
        print(f"   - Prompt: {story_prompt}")
        print(f"   - Scenes requested: {num_scenes}")
        print(f"   - Total parts generated: {story_data.get('total_parts', 'N/A')}")
        print(f"   - Model used: {story_data.get('model', 'N/A')}")
        
        return True
    else:
        print("❌ Step 5: Story generation failed")
        return False

def interactive_demo():
    """Run an interactive demo where user can specify the story."""
    print("🎨 Interactive Demo: Custom Story Generator")
    print("=" * 50)
    
    # Test API first
    if not test_api_connection():
        print("❌ API test failed. Please check your setup.")
        return False
    
    # Get user input
    story_prompt = input("\n📝 Enter your story idea: ").strip()
    if not story_prompt:
        story_prompt = "A magical adventure in a enchanted forest"
        print(f"Using default: {story_prompt}")
    
    try:
        num_scenes = int(input("How many scenes (1-6 recommended for demo): ") or "3")
        num_scenes = max(1, min(num_scenes, 6))  # Limit for demo
    except ValueError:
        num_scenes = 3
        print(f"Using default: {num_scenes} scenes")
    
    print(f"\n⏱️  Estimated time: {num_scenes * 6 / 60:.1f} minutes")
    proceed = input("Continue? (y/n): ").strip().lower()
    
    if proceed not in ['y', 'yes', '']:
        print("Demo cancelled.")
        return False
    
    # Setup and run generation
    project_dir = Path(__file__).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_dir / "generated_stories" / f"interactive_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    client = setup_client()
    story_data = generate_custom_story_with_images(
        client=client,
        story_prompt=story_prompt,
        num_scenes=num_scenes,
        output_dir=output_dir
    )
    
    if story_data:
        html_path = create_html_display(story_data, output_dir)
        print(f"\n🎉 Your story is ready!")
        print(f"💻 Open: {html_path}")
        return True
    else:
        print("❌ Story generation failed")
        return False

if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Quick Demo (auto-generated 2-scene story)")
    print("2. Interactive Demo (your custom story)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        success = quick_demo()
    elif choice == "2":
        success = interactive_demo()
    elif choice == "3":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice. Running quick demo...")
        success = quick_demo()
    
    if success:
        print("\n✅ Demo completed successfully!")
        print("🔧 The picture book generator is working properly!")
    else:
        print("\n❌ Demo failed. Please check the troubleshooting guide in README_FIXES.md")
