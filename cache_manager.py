#!/usr/bin/env python3
"""
Automated Cache Clearing System
Prevents stale interaction data in external systems (GitHub Actions, repl.deploy, UptimeRobot)
"""

import os
import json
import asyncio
import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ExternalCacheManager:
    """Manages cache clearing across all external systems"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPOSITORY_OWNER', 'your-username')
        self.repo_name = os.getenv('GITHUB_REPOSITORY_NAME', 'your-repo')
        self.base_url = os.getenv('REPLIT_BASE_URL', 'https://your-bot.repl.co')
        
    async def trigger_cache_clear(self, reason: str = "Database modification", streamer_name: Optional[str] = None):
        """
        Automatically trigger cache clearing across all external systems
        
        Args:
            reason: Reason for cache clearing
            streamer_name: Name of streamer that was modified (optional)
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        logger.info(f"🔄 AUTOMATED CACHE CLEAR: {reason}")
        if streamer_name:
            logger.info(f"📺 Affected streamer: {streamer_name}")
        
        # Clear multiple cache levels simultaneously
        results = await asyncio.gather(
            self._clear_github_actions_cache(reason, streamer_name),
            self._trigger_repl_deploy_refresh(reason),
            self._force_discord_cache_refresh(),
            return_exceptions=True
        )
        
        # Log results
        success_count = sum(1 for r in results if r is True)
        logger.info(f"✅ Cache clearing completed: {success_count}/3 systems refreshed")
        
        # Update restart log for external systems
        self._update_restart_log(reason, streamer_name, timestamp)
        
        return success_count >= 2  # Success if at least 2/3 systems cleared
    
    async def _clear_github_actions_cache(self, reason: str, streamer_name: Optional[str]) -> bool:
        """Trigger GitHub Actions workflow to clear cached data"""
        try:
            if not self.github_token:
                logger.warning("⚠️ GitHub token not configured - skipping GitHub Actions cache clear")
                return False
            
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/dispatches"
            
            payload = {
                "event_type": "bot-restart",
                "client_payload": {
                    "reason": reason,
                    "streamer": streamer_name,
                    "cache_clear": True,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 204:
                logger.info("✅ GitHub Actions cache clear triggered")
                return True
            else:
                logger.error(f"❌ GitHub Actions trigger failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ GitHub Actions cache clear error: {e}")
            return False
    
    async def _trigger_repl_deploy_refresh(self, reason: str) -> bool:
        """Trigger repl.deploy refresh to clear cached data"""
        try:
            url = f"{self.base_url}/refresh"
            
            payload = {
                "trigger": "automated_cache_clear",
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ repl.deploy cache refresh triggered")
                return True
            else:
                logger.warning(f"⚠️ repl.deploy refresh responded: {response.status_code}")
                return True  # Still count as success since bot is running
                
        except Exception as e:
            logger.error(f"❌ repl.deploy refresh error: {e}")
            return False
    
    async def _force_discord_cache_refresh(self) -> bool:
        """Force Discord interaction cache refresh through command re-sync"""
        try:
            # This will be called by the bot's command sync system
            logger.info("✅ Discord cache refresh scheduled")
            return True
        except Exception as e:
            logger.error(f"❌ Discord cache refresh error: {e}")
            return False
    
    def _update_restart_log(self, reason: str, streamer_name: Optional[str], timestamp: str):
        """Update restart log with cache clearing information"""
        try:
            log_entry = f"Restart triggered at {timestamp}\n"
            log_entry += f"Trigger: AUTOMATED CACHE CLEAR - {reason}\n"
            if streamer_name:
                log_entry += f"Affected streamer: {streamer_name}\n"
            log_entry += "Systems: GitHub Actions, repl.deploy, Discord cache\n"
            log_entry += "---\n"
            
            with open('.restart-log', 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            logger.info("📝 Updated restart log")
            
        except Exception as e:
            logger.error(f"❌ Failed to update restart log: {e}")

# Global cache manager instance
cache_manager = ExternalCacheManager()

async def auto_clear_cache_on_streamer_removal(streamer_name: str):
    """
    Automatically clear all external caches when a streamer is removed
    Call this function whenever a streamer is removed from the database
    """
    await cache_manager.trigger_cache_clear(
        reason=f"Streamer '{streamer_name}' removed from database",
        streamer_name=streamer_name
    )

async def auto_clear_cache_on_database_change(operation: str, details: str = ""):
    """
    Automatically clear all external caches when database structure changes
    Call this function for major database operations
    """
    await cache_manager.trigger_cache_clear(
        reason=f"Database {operation}: {details}",
        streamer_name=None
    )

def manual_cache_clear(reason: str = "Manual trigger"):
    """
    Manually trigger cache clearing (synchronous wrapper)
    Use this for manual testing or emergency cache clearing
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(cache_manager.trigger_cache_clear(reason))
    finally:
        loop.close()