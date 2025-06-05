"""
Exploration management module - Simplified
"""

import asyncio
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ExplorationManager:
    """Handles exploration - simplified version"""
    
    def __init__(self, client, config, parser):
        self.client = client
        self.config = config
        self.parser = parser
        
    async def explore(self, chat):
        """Start exploration - now handled in main loop"""
        # This is now just a placeholder since exploration is handled directly in game_bot.py
        pass
