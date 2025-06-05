"""
Inventory management module
"""

import asyncio
from utils.logger import setup_logger

logger = setup_logger(__name__)


class InventoryManager:
    """Handles inventory and item usage"""
    
    def __init__(self, client, config, parser):
        self.client = client
        self.config = config
        self.parser = parser
        
    async def open_inventory(self, chat):
        """Open inventory"""
        try:
            await self.client.send_message(chat, "🎒 Інвентар")
            await asyncio.sleep(self.config.MESSAGE_READ_DELAY)
            return True
        except Exception as e:
            logger.error(f"Error opening inventory: {e}")
            return False
    
    async def get_inventory_items(self, chat):
        """Get list of items in inventory"""
        try:
            # Open inventory
            await self.open_inventory(chat)
            
            # Get messages
            messages = await self.client.get_messages(chat, limit=10)
            
            items = []
            for msg in messages:
                if msg.text and "Кількість:" in msg.text:
                    item = self.parser.parse_inventory_item(msg.text)
                    if item:
                        items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting inventory items: {e}")
            return []
    
    async def use_energy_item(self, chat):
        """Try to use an energy restoration item"""
        try:
            # Get inventory
            items = await self.get_inventory_items(chat)
            
            # Look for energy items
            for item in items:
                if "Коробка цукерок" in item.get('name', '') or "+10 ЕН" in item.get('effect', ''):
                    logger.info(f"Found energy item: {item['name']}")
                    
                    # Use item (need to implement item usage logic)
                    # For now, we'll need to figure out how to click on items
                    
                    # Get recent messages with buttons
                    messages = await self.client.get_messages(chat, limit=10)
                    
                    for msg in messages:
                        if msg.buttons and item['name'] in msg.text:
                            # Click use button (usually the first button)
                            await msg.click(0)
                            logger.info(f"Used {item['name']}")
                            await asyncio.sleep(self.config.BUTTON_CLICK_DELAY)
                            return True
            
            logger.info("No energy items found")
            return False
            
        except Exception as e:
            logger.error(f"Error using energy item: {e}")
            return False
    
    async def equip_item(self, chat, item_name):
        """Equip an item from inventory"""
        try:
            # Open inventory
            await self.open_inventory(chat)
            await asyncio.sleep(self.config.MESSAGE_READ_DELAY)
            
            # Find item in messages
            messages = await self.client.get_messages(chat, limit=20)
            
            for msg in messages:
                if msg.text and item_name in msg.text and msg.buttons:
                    # Click equip button (need to determine which button)
                    await msg.click(0)  # Assuming first button is equip
                    logger.info(f"Equipped {item_name}")
                    await asyncio.sleep(self.config.BUTTON_CLICK_DELAY)
                    return True
            
            logger.warning(f"Item {item_name} not found in inventory")
            return False
            
        except Exception as e:
            logger.error(f"Error equipping item: {e}")
            return False
