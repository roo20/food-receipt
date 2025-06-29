#!/usr/bin/env python3
"""
Font Testing Script for Docker Environment
This script helps diagnose font availability in different environments.
"""

import os
import sys
import platform
from PIL import Image, ImageDraw, ImageFont
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_font_availability():
    """Test font availability on the current platform"""
    print(f"Platform: {platform.system()}")
    print(f"Python version: {sys.version}")
    print()
    
    # List common font directories
    font_dirs = [
        "/usr/share/fonts/",
        "/usr/local/share/fonts/",
        "/System/Library/Fonts/",
        "C:\\Windows\\Fonts\\",
    ]
    
    print("Available font directories:")
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            print(f"✓ {font_dir}")
            try:
                fonts = os.listdir(font_dir)
                print(f"  Found {len(fonts)} files")
                # Show first few font files
                ttf_fonts = [f for f in fonts if f.endswith(('.ttf', '.otf'))][:5]
                if ttf_fonts:
                    print(f"  Sample fonts: {', '.join(ttf_fonts)}")
            except PermissionError:
                print(f"  (Permission denied)")
        else:
            print(f"✗ {font_dir}")
    print()
    
    # Test specific fonts
    fonts_to_test = [
        # Linux fonts
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        # Generic names that might work
        "DejaVuSansMono.ttf",
        "LiberationMono-Regular.ttf",
        "FreeMono.ttf",
        # Windows fonts
        "consola.ttf",
        "arial.ttf",
        "arialbd.ttf",
    ]
    
    print("Testing specific fonts:")
    for font_path in fonts_to_test:
        try:
            font = ImageFont.truetype(font_path, 20)
            print(f"✓ {font_path} - SUCCESS")
        except (OSError, IOError) as e:
            print(f"✗ {font_path} - FAILED: {e}")
    
    print()
    
    # Test creating an image with fonts
    print("Testing image creation with fonts:")
    try:
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try default font
        default_font = ImageFont.load_default()
        draw.text((10, 10), "REWE Test", fill='black', font=default_font)
        print("✓ Default font works")
        
        # Try to find a working font
        working_font = None
        for font_path in fonts_to_test:
            try:
                working_font = ImageFont.truetype(font_path, 20)
                draw.text((10, 30), "REWE Test", fill='black', font=working_font)
                print(f"✓ Working font found: {font_path}")
                break
            except (OSError, IOError):
                continue
        
        if not working_font:
            print("✗ No TrueType fonts working, using default only")
        
        # Save test image
        img.save('font_test.png')
        print("✓ Test image saved as 'font_test.png'")
        
    except Exception as e:
        print(f"✗ Image creation failed: {e}")

if __name__ == "__main__":
    test_font_availability()
