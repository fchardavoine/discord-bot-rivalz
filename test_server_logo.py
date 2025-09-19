#!/usr/bin/env python3
"""Test script to verify server logo functionality"""

import asyncio
import aiohttp
import io
from PIL import Image, ImageDraw, ImageFont

async def test_server_logo():
    """Test downloading and placing a server logo"""
    
    # Test with a known Discord server icon URL
    test_icon_url = "https://cdn.discordapp.com/icons/1107832291260121218/a_1234567890abcdef.png"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Try to download icon
            try:
                async with session.get(test_icon_url) as resp:
                    if resp.status == 200:
                        icon_data = await resp.read()
                        print(f"✅ Downloaded {len(icon_data)} bytes of server icon")
                    else:
                        print(f"❌ Failed to download icon: {resp.status}")
                        return
            except Exception as e:
                print(f"❌ Error downloading icon: {e}")
                return
            
            # Create test image
            img = Image.new('RGB', (800, 400), color='#36393F')
            draw = ImageDraw.Draw(img)
            
            # Load font
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            # Process server icon
            icon_img = Image.open(io.BytesIO(icon_data))
            icon_img = icon_img.convert('RGBA')
            icon_size = 48
            icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            
            # Create circular mask
            mask = Image.new('L', (icon_size, icon_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, icon_size, icon_size), fill=255)
            
            # Apply mask
            icon_circular = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
            icon_circular.paste(icon_img, mask=mask)
            
            # Add welcome text
            welcome_text = "Welcome to RIVALZ MLB THE SHOW!"
            text_bbox = draw.textbbox((0, 0), welcome_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (800 - text_width) // 2
            text_y = 40
            
            # Position logo to left of text
            logo_x = text_x - icon_size - 15
            logo_y = text_y + (text_bbox[3] - text_bbox[1] - icon_size) // 2
            
            # Place logo
            img.paste(icon_circular, (logo_x, logo_y), icon_circular)
            
            # Draw text
            draw.text((text_x, text_y), welcome_text, font=font, fill=(255, 215, 0))
            
            # Save test image
            img.save('test_logo_output.png')
            print("✅ Test image saved as test_logo_output.png")
            print(f"Logo positioned at ({logo_x}, {logo_y})")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_server_logo())