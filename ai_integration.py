import os
import json
import logging
from typing import Optional

import discord
from openai import OpenAI
from google import genai
from google.genai import types

# Initialize AI clients
openai_client = None
gemini_client = None

def initialize_ai_clients():
    """Initialize AI clients if API keys are available"""
    global openai_client, gemini_client
    
    # Initialize OpenAI client
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        openai_client = OpenAI(api_key=openai_key)
        logging.info("OpenAI client initialized")
    
    # Initialize Gemini client
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        gemini_client = genai.Client(api_key=gemini_key)
        logging.info("Gemini client initialized")

async def chat_with_gpt(message: str, user_name: str = "User") -> str:
    """Chat with ChatGPT"""
    if not openai_client:
        return "❌ OpenAI API key not configured. Please ask an admin to set up the OPENAI_API_KEY."
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a helpful Discord bot assistant. The user's name is {user_name}. Keep responses concise and friendly for Discord chat."
                },
                {"role": "user", "content": message}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return f"❌ Error communicating with ChatGPT: {str(e)}"

async def chat_with_gemini(message: str, user_name: str = "User") -> str:
    """Chat with Google Gemini"""
    if not gemini_client:
        return "❌ Gemini API key not configured. Please ask an admin to set up the GEMINI_API_KEY."
    
    try:
        system_prompt = f"You are a helpful Discord bot assistant. The user's name is {user_name}. Keep responses concise and friendly for Discord chat."
        
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(role="user", parts=[types.Part(text=f"{system_prompt}\n\nUser: {message}")])
            ]
        )
        
        return response.text or "Sorry, I couldn't generate a response."
    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        return f"❌ Error communicating with Gemini: {str(e)}"

async def analyze_image_with_gpt(image_url: str, prompt: str = "Describe this image") -> str:
    """Analyze an image with ChatGPT Vision"""
    if not openai_client:
        return "❌ OpenAI API key not configured."
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI Vision API error: {e}")
        return f"❌ Error analyzing image: {str(e)}"

async def analyze_image_with_gemini(image_url: str, prompt: str = "Describe this image") -> str:
    """Analyze an image with Gemini Vision"""
    if not gemini_client:
        return "❌ Gemini API key not configured."
    
    try:
        # Download image data
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    return "❌ Could not download image for analysis."
                image_data = await resp.read()
        
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
                prompt
            ]
        )
        
        return response.text or "Sorry, I couldn't analyze the image."
    except Exception as e:
        logging.error(f"Gemini Vision API error: {e}")
        return f"❌ Error analyzing image: {str(e)}"

def get_ai_status() -> dict:
    """Get status of AI integrations"""
    return {
        "openai": openai_client is not None,
        "gemini": gemini_client is not None,
        "openai_key": "OPENAI_API_KEY" in os.environ,
        "gemini_key": "GEMINI_API_KEY" in os.environ
    }