#!/usr/bin/env python3
"""
Simple test script to validate the Gemini API connection and basic functionality.
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

def test_api():
    """Test basic API functionality."""
    print("🔍 Testing Google Gemini API connection...")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ No API key found in .env file")
        return False
    
    try:
        # Initialize client
        client = genai.Client(api_key=api_key)
        print("✅ Client initialized successfully")
        
        # Test simple text generation
        print("🧪 Testing text generation...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents="Hello! Please respond with 'API test successful' if you can hear me."
        )
        
        if response and response.candidates:
            text_content = response.candidates[0].content.parts[0].text
            print(f"✅ Text response: {text_content}")
            
            # Test image generation
            print("🖼️  Testing image generation...")
            image_response = client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents="Generate a simple cartoon cat sitting on a sunny windowsill",
                config=types.GenerateContentConfig(
                    response_modalities=["Text", "Image"]
                )
            )
            
            if image_response and image_response.candidates:
                parts = image_response.candidates[0].content.parts
                print(f"✅ Image generation response has {len(parts)} parts")
                
                for i, part in enumerate(parts):
                    if hasattr(part, 'text') and part.text:
                        print(f"   Part {i}: Text content found")
                    elif hasattr(part, 'inline_data') and part.inline_data:
                        print(f"   Part {i}: Image data found")
                    else:
                        print(f"   Part {i}: Unknown part type")
                
                return True
            else:
                print("❌ Image generation failed - no response")
                return False
        else:
            print("❌ Text generation failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    if success:
        print("\n🎉 All tests passed! The picture book generator should work now.")
    else:
        print("\n😞 Tests failed. Please check your API key and internet connection.")
