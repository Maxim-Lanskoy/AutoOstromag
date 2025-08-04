#!/usr/bin/env python3
"""
Buying Bot for AutoOstromag - Specialized bot for purchasing resources
Navigates through the game interface to buy items from the shop
"""

import asyncio
import sys
import re
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BuyingBot:
    """
    Specialized bot for buying resources from the game shop
    """
    
    def __init__(self, client, config, item_to_buy="Шкіряні Чоботи", quantity=100):
        """Initialize buying bot with client and configuration"""
        self.client = client
        self.config = config
        self.game_chat = None
        self.item_to_buy = item_to_buy
        self.quantity = quantity
        self.purchases_made = 0
        self.is_running = False
    
    async def human_delay(self, min_seconds=None, max_seconds=None):
        """Simulate human-like reaction time"""
        import random
        if min_seconds is None:
            min_seconds = self.config.HUMAN_DELAY_MIN
        if max_seconds is None:
            max_seconds = self.config.HUMAN_DELAY_MAX
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def send_start_command(self):
        """Send /start command to refresh the game keyboard"""
        logger.info("Sending /start command to refresh game menu...")
        await self.human_delay(2, 4)
        await self.client.send_message(self.game_chat, '/start')
        await asyncio.sleep(3)
        logger.info("Game menu refreshed")
    
    async def navigate_to_town(self):
        """Navigate to the town (Місто)"""
        logger.info("Navigating to town...")
        await self.human_delay()
        
        # Look for the main menu with town button
        messages = await self.client.get_messages(self.game_chat, limit=3)
        
        for msg in messages:
            if msg.buttons:
                for row_idx, row in enumerate(msg.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and "Місто" in btn.text:
                            await self.human_delay()
                            await msg.click(row_idx, btn_idx)
                            logger.info("Clicked 'Місто' button")
                            await asyncio.sleep(3)
                            return True
        
        logger.error("Could not find 'Місто' button")
        return False
    
    async def navigate_to_shop(self):
        """Navigate to the shop (Крамниця)"""
        logger.info("Navigating to shop...")
        await self.human_delay()
        
        # Look for town menu with shop button
        messages = await self.client.get_messages(self.game_chat, limit=3)
        
        for msg in messages:
            if msg.buttons:
                for row_idx, row in enumerate(msg.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and "Крамниця" in btn.text:
                            await self.human_delay()
                            await msg.click(row_idx, btn_idx)
                            logger.info("Clicked 'Крамниця' button")
                            await asyncio.sleep(3)
                            return True
        
        logger.error("Could not find 'Крамниця' button")
        return False
    
    async def click_buy_items(self):
        """Click on 'Купити предмети' button"""
        logger.info("Looking for 'Купити предмети' button...")
        await self.human_delay()
        
        messages = await self.client.get_messages(self.game_chat, limit=3)
        
        for msg in messages:
            if msg.buttons:
                for row_idx, row in enumerate(msg.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and "Купити предмети" in btn.text:
                            await self.human_delay()
                            await msg.click(row_idx, btn_idx)
                            logger.info("Clicked 'Купити предмети' button")
                            await asyncio.sleep(3)
                            return True
        
        logger.error("Could not find 'Купити предмети' button")
        return False
    
    async def select_item_to_buy(self):
        """Select the item to buy (first button by default - Шкіряні Чоботи)"""
        logger.info(f"Looking for '{self.item_to_buy}' to buy...")
        await self.human_delay()
        
        messages = await self.client.get_messages(self.game_chat, limit=3)
        
        for msg in messages:
            if msg.buttons:
                # Click the first button (leather boots)
                if len(msg.buttons) > 0 and len(msg.buttons[0]) > 0:
                    await self.human_delay()
                    await msg.click(0, 0)
                    logger.info(f"Clicked first item button (expecting '{self.item_to_buy}')")
                    await asyncio.sleep(3)
                    return True
        
        logger.error("Could not find item selection buttons")
        return False
    
    
    async def check_purchase_success(self):
        """Check if the purchase was successful and wait for success message"""
        # Wait for success message to appear
        await asyncio.sleep(2)
        
        messages = await self.client.get_messages(self.game_chat, limit=10)
        
        for msg in messages:
            if msg.text:
                # Look for success message
                if "Успішно придбано" in msg.text and "золота" in msg.text:
                    self.purchases_made += 1
                    logger.info(f"Purchase successful! Total purchases: {self.purchases_made}/{self.quantity}")
                    return True
                # Check for insufficient funds
                elif "Недостатньо золота" in msg.text or "недостатньо" in msg.text.lower():
                    logger.error("Insufficient gold to make purchase!")
                    return False
        
        logger.warning("No clear success message found, but continuing...")
        self.purchases_made += 1
        return True
    
    
    async def start_buying_process(self):
        """Main buying process"""
        try:
            logger.info("=== BUYING BOT STARTING ===")
            
            # Connect to game bot
            self.game_chat = await self.client.get_entity(self.config.GAME_BOT_USERNAME)
            logger.info(f"Connected to game bot: {self.game_chat.username}")
            
            # Send /start to refresh menu
            await self.send_start_command()
            
            # Navigate to town
            if not await self.navigate_to_town():
                raise Exception("Failed to navigate to town")
            
            # Navigate to shop
            if not await self.navigate_to_shop():
                raise Exception("Failed to navigate to shop")
            
            # Click buy items
            if not await self.click_buy_items():
                raise Exception("Failed to find buy items button")
            
            # Select the item to buy (one time only)
            if not await self.select_item_to_buy():
                raise Exception("Failed to select item to buy")
            
            # Start buying loop - dynamically find buying message each time
            self.is_running = True
            
            while self.is_running and self.purchases_made < self.quantity:
                logger.info(f"Starting purchase {self.purchases_made + 1}/{self.quantity}")
                
                # Always search for the buying message dynamically (to handle unlimited purchases)
                buying_message = None
                # Start with reasonable limit, increase if needed
                for search_limit in [20, 50, 100, 200]:
                    messages = await self.client.get_messages(self.game_chat, limit=search_limit)
                    
                    for msg in messages:
                        # Look for message with item details and buy button
                        if msg.buttons and msg.text:
                            # Check if this is the item details message (has item name and characteristics)
                            if self.item_to_buy in msg.text or ("Характеристики:" in msg.text and "Ціна:" in msg.text):
                                # Check if it has a buy button
                                for row in msg.buttons:
                                    for btn in row:
                                        if btn.text and ("Купити за" in btn.text or "💰" in btn.text):
                                            buying_message = msg
                                            logger.info(f"Found buying message with item details (searched {search_limit} messages)")
                                            break
                                    if buying_message:
                                        break
                        
                        if buying_message:
                            break
                    
                    if buying_message:
                        break
                    
                    logger.warning(f"Buying message not found in {search_limit} messages, trying larger search...")
                
                if not buying_message:
                    logger.error("Could not find buying message after extensive search")
                    logger.error("This might mean the buying interface disappeared or changed")
                    break
                
                # Find and click the buy button
                buy_button_found = False
                for row_idx, row in enumerate(buying_message.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and ("Купити за" in btn.text or "💰" in btn.text):
                            await buying_message.click(row_idx, btn_idx)
                            logger.info(f"Clicked buy button (purchase #{self.purchases_made + 1})")
                            buy_button_found = True
                            break
                    if buy_button_found:
                        break
                
                if not buy_button_found:
                    logger.error("Could not find buy button on message")
                    break
                
                # Check if purchase was successful
                if not await self.check_purchase_success():
                    logger.error("Purchase failed or insufficient funds. Stopping...")
                    break
            
            # Buying complete
            logger.info(f"=== BUYING COMPLETE ===")
            logger.info(f"Total purchases made: {self.purchases_made}/{self.quantity}")
            
            # Return to main menu
            await self.send_start_command()
            
            # Stop the process
            self.is_running = False
            logger.info("Buying bot finished successfully")
            
        except Exception as e:
            logger.error(f"Error in buying process: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the buying bot"""
        self.is_running = False
        logger.info("Buying bot stopped")


async def main():
    """Main function to run the buying bot"""
    config = Config()
    
    # Parse command line arguments for customization
    import argparse
    parser = argparse.ArgumentParser(description='AutoOstromag Buying Bot')
    parser.add_argument('--item', default='Шкіряні Чоботи', help='Item to buy (default: Шкіряні Чоботи)')
    parser.add_argument('--quantity', type=int, default=100, help='Quantity to buy (default: 100)')
    args = parser.parse_args()
    
    # Create client
    client = TelegramClient(
        config.SESSION_NAME,
        config.API_ID,
        config.API_HASH
    )
    
    try:
        # Connect and authorize
        await client.start()
        logger.info("Client connected successfully")
        
        # Initialize buying bot
        buying_bot = BuyingBot(client, config, args.item, args.quantity)
        
        # Start the buying process
        await buying_bot.start_buying_process()
        
        logger.info("Buying bot completed. Exiting...")
        
    except KeyboardInterrupt:
        logger.info("Buying bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await client.disconnect()
        logger.info("Client disconnected")
        # Exit the process entirely
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
