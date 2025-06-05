"""
Character management module
"""

import asyncio
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CharacterManager:
    """Handles character information and stats"""
    
    def __init__(self, client, config, parser):
        self.client = client
        self.config = config
        self.parser = parser
        
    async def get_character_info(self, chat):
        """Get current character information"""
        try:
            # Send character command
            await self.client.send_message(chat, "🧍 Персонаж")
            await asyncio.sleep(self.config.MESSAGE_READ_DELAY)
            
            # Get response
            messages = await self.client.get_messages(chat, limit=3)
            
            for msg in messages:
                if msg.text and "Рівень" in msg.text and "Здоров'я:" in msg.text:
                    char_info = self.parser.parse_character_info(msg.text)
                    if char_info:
                        return char_info
            
            logger.error("Failed to get character info")
            return None
            
        except Exception as e:
            logger.error(f"Error getting character info: {e}")
            return None
    
    async def check_equipment(self, chat):
        """Check equipped items"""
        try:
            # First get character info
            await self.client.send_message(chat, "🧍 Персонаж")
            await asyncio.sleep(self.config.MESSAGE_READ_DELAY)
            
            # Get equipment info (it comes after character stats)
            messages = await self.client.get_messages(chat, limit=5)
            
            for msg in messages:
                if msg.text and "Спорядження героя" in msg.text:
                    equipment = self.parser.parse_equipment(msg.text)
                    if equipment:
                        return equipment
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking equipment: {e}")
            return None
