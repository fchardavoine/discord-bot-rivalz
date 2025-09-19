#!/usr/bin/env python3
"""
Deployment fix script - ensures all requirements are met for successful deployment.
Run this before attempting to redeploy.
"""

import os
import sys
import logging
import time
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all environment variables are set"""
    required_vars = ['DISCORD_TOKEN']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        return False
    
    logger.info("All required environment variables are set")
    return True

def check_dependencies():
    """Check if all dependencies can be imported"""
    try:
        import discord
        import flask
        import requests
        logger.info("All critical dependencies can be imported")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False

def test_bot_initialization():
    """Test if the bot can initialize without errors"""
    try:
        # Quick test of bot initialization components
        from bot import DiscordBot
        logger.info("Bot class can be imported successfully")
        return True
    except Exception as e:
        logger.error(f"Bot initialization test failed: {e}")
        return False

def check_flask_app():
    """Test if Flask app can start"""
    try:
        from main import app
        logger.info("Flask app can be imported successfully")
        return True
    except Exception as e:
        logger.error(f"Flask app test failed: {e}")
        return False

def main():
    """Run all deployment readiness checks"""
    logger.info("Running deployment readiness checks...")
    
    checks = [
        ("Environment Variables", check_environment),
        ("Dependencies", check_dependencies),
        ("Bot Initialization", test_bot_initialization),
        ("Flask App", check_flask_app)
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        logger.info(f"Checking {name}...")
        if not check_func():
            all_passed = False
            logger.error(f"FAILED: {name}")
        else:
            logger.info(f"PASSED: {name}")
    
    if all_passed:
        logger.info("All deployment checks PASSED - Ready for deployment!")
        logger.info("You can now attempt to redeploy your application.")
        return 0
    else:
        logger.error("Some deployment checks FAILED - Please fix issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())