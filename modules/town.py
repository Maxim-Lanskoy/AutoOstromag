"""
Town management module
"""

import asyncio
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TownManager:
    """Handles town actions like healing, shopping, etc."""
    
    def __init__(self, client, config, parser):
        self.client = client
        self.config = config
        self.parser = parser
        
    async def go_to_town(self, chat):
        """Go to town"""
        try:
            await self.client.send_message(chat, "🏡 Місто")
            await asyncio.sleep(self.config.MESSAGE_READ_DELAY)
            
            # Check if we're in town
            messages = await self.client.get_messages(chat, limit=2)
            for msg in messages:
                if msg.text and "Вітаємо в місті" in msg.text:
                    logger.info("Arrived in town")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error going to town: {e}")
            return False
    
    async def heal_character(self, chat, char_info):
        """Heal character at healer"""
        try:
            # Go to town first
            if not await self.go_to_town(chat):
                logger.error("Failed to go to town")
                return False
            
            # Go to healer
            await self.client.send_message(chat, "💚 Цілитель")
            await asyncio.sleep(self.config.MESSAGE_READ_DELAY)
            
            # Check healer response
            messages = await self.client.get_messages(chat, limit=3)
            
            for msg in messages:
                if msg.text and "Вартість лікування" in msg.text:
                    # Parse healing cost
                    heal_info = self.parser.parse_heal_cost(msg.text)
                    if heal_info:
                        cost = heal_info['cost']
                        health_to_heal = heal_info['health_to_heal']
                        
                        logger.info(f"Healing cost: {cost} gold for {health_to_heal} HP")
                        
                        # Check if we have enough gold
                        if char_info['gold'] >= cost:
                            # Find and click heal button
                            if msg.buttons:
                                await msg.click(0)  # Assuming first button is heal
                                logger.info(f"Healed for {cost} gold")
                                await asyncio.sleep(self.config.BUTTON_CLICK_DELAY)
                                
                                # Go back to main menu
                                await self.client.send_message(chat, "🔙 Назад")
                                await asyncio.sleep(self.config.BUTTON_CLICK_DELAY)
                                
                                return True
                        else:
                            logger.warning(f"Not enough gold for healing. Have: {char_info['gold']}, Need: {cost}")
                            # Go back
                            await self.client.send_message(chat, "🔙 Назад")
                            await asyncio.sleep(self.config.BUTTON_CLICK_DELAY)
                            return False
            
            logger.error("Failed to find heal information")
            return False
            
        except Exception as e:
            logger.error(f"Error healing character: {e}")
            return False
    
    # AUTO-BUY DISABLED - Commented out for now
    # async def buy_item(self, chat, item_name, char_info):
    #     """Buy item from shop"""
    #     try:
    #         # Go to town
    #         if not await self.go_to_town(chat):
    #             return False
    #         
    #         # Go to shop
    #         await self.client.send_message(chat, "🏪 Крамниця")
    #         await asyncio.sleep(self.config.MESSAGE_READ_DELAY)
    #         
    #         # Look for item in shop
    #         found = False
    #         page = 1
    #         max_pages = 5
    #         
    #         while page <= max_pages and not found:
    #             messages = await self.client.get_messages(chat, limit=15)
    #             
    #             for msg in messages:
    #                 if msg.text and item_name in msg.text and "Ціна:" in msg.text:
    #                     # Parse item info
    #                     item_info = self.parser.parse_shop_item(msg.text)
    #                     if item_info:
    #                         price = item_info['price']
    #                         
    #                         if char_info['gold'] >= price:
    #                             # Buy item
    #                             if msg.buttons:
    #                                 await msg.click(0)  # Assuming first button is buy
    #                                 logger.info(f"Bought {item_name} for {price} gold")
    #                                 found = True
    #                                 break
    #                         else:
    #                             logger.warning(f"Not enough gold for {item_name}. Have: {char_info['gold']}, Need: {price}")
    #                             found = True  # Stop searching
    #                             break
    #             
    #             if not found:
    #                 # Try next page
    #                 # Look for next page button
    #                 for msg in messages:
    #                     if msg.buttons and "Сторінка" in msg.text:
    #                         # Click next page (usually second button)
    #                         if len(msg.buttons[0]) > 1:
    #                             await msg.buttons[0][1].click()
    #                             await asyncio.sleep(self.config.BUTTON_CLICK_DELAY)
    #                             page += 1
    #                             break
    #                 else:
    #                     # No more pages
    #                     break
    #         
    #         # Go back to main menu
    #         await self.client.send_message(chat, "🔙 Назад")
    #         await asyncio.sleep(self.config.BUTTON_CLICK_DELAY)
    #         
    #         return found
    #         
    #     except Exception as e:
    #         logger.error(f"Error buying item: {e}")
    #         return False
