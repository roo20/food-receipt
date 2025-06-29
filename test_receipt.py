#!/usr/bin/env python3
"""
Test script for the food receipt generator
Run this to test receipt generation without Telegram bot
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_simple import FoodReceiptGenerator

def test_receipt_generation():
    """Test generating a few receipts"""
    print("Testing receipt generation...")
    
    generator = FoodReceiptGenerator()
    
    # Test getting working days
    print("\n1. Testing working days calculation:")
    working_days = generator.get_working_days(5)
    for i, day in enumerate(working_days, 1):
        print(f"   Day {i}: {day.strftime('%A, %d.%m.%Y')}")
    
    # Test generating receipt data
    print("\n2. Testing receipt data generation:")
    test_date = datetime.now() - timedelta(days=1)
    receipt_data = generator.generate_receipt_data(test_date)
    print(f"   Date: {receipt_data['date']}")
    print(f"   Total: EUR {receipt_data['total']:.2f}")
    print(f"   Items: {len(receipt_data['items'])}")
    for item in receipt_data['items']:
        print(f"     - {item['name']}: EUR {item['price']:.2f}")
    
    # Test generating receipt image
    print("\n3. Testing receipt image generation:")
    try:
        png_data = generator.create_receipt_image(test_date)
        print(f"   Generated PNG image: {len(png_data)} bytes")
        
        # Save test image
        with open("test_receipt.png", "wb") as f:
            f.write(png_data)
        print("   Saved test image as 'test_receipt.png'")
        
    except Exception as e:
        print(f"   Error generating image: {e}")
        return False
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_receipt_generation()
    if success:
        print("\nYou can now run the Telegram bot with: python main_simple.py")
        print("(Make sure to configure your bot token and user ID in config.py first)")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
        sys.exit(1)
