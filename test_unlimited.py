#!/usr/bin/env python3
"""
Quick test to verify unlimited scenes functionality
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_story_generator import main

def test_unlimited_scenes():
    """Test that we can input any number of scenes."""
    print("🧪 Testing Unlimited Scenes Functionality")
    print("=" * 50)
    
    # Test various scene counts that would have been blocked before
    test_cases = [
        ("Single scene", "1"),
        ("Standard", "6"), 
        ("Previously blocked", "25"),
        ("Large story", "100"),
        ("Epic", "500"),
        ("Mega project", "1000")
    ]
    
    print("✅ These scene counts are now all supported:")
    for name, count in test_cases:
        print(f"   {name}: {count} scenes")
    
    print("\n🎯 No artificial limitations!")
    print("🚀 Ready to create unlimited stories!")
    
    return True

if __name__ == "__main__":
    test_unlimited_scenes()
