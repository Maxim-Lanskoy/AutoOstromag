#!/usr/bin/env python3
"""
Disassembly Bot for AutoOstromag - Specialized bot for disassembling leather boots
Navigates through inventory to find and dismantle leather boots for crafting materials
"""

import asyncio
import sys
import re
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DisassemblyBot:
    """
    Specialized bot for disassembling leather boots from inventory
    """
    
    def __init__(self, client, config, item_to_disassemble="Шкіряні Чоботи"):
        """Initialize disassembly bot with client and configuration"""
        self.client = client
        self.config = config
        self.game_chat = None
        self.item_to_disassemble = item_to_disassemble
        self.items_disassembled = 0
        self.is_running = False
        self.inventory_message = None  # Store inventory message reference
        self.dont_rush_count = 0  # Track how many times we've seen don't rush
    
    async def human_delay(self, seconds=1):
        """Fast delay for speedy operation"""
        await asyncio.sleep(seconds)
    
    async def send_start_command(self):
        """Send /start command to refresh the game keyboard"""
        logger.info("Sending /start command to refresh game menu...")
        await self.human_delay(1)
        await self.client.send_message(self.game_chat, '/start')
        await asyncio.sleep(2)
        logger.info("Game menu refreshed")
    
    async def navigate_to_inventory(self, retry_count=0):
        """Navigate to inventory (Інвентар) with unlimited retries"""
        logger.info(f"Navigating to inventory... (attempt {retry_count + 1})")
        await self.human_delay()
        
        # Look for the main menu with inventory button
        messages = await self.client.get_messages(self.game_chat, limit=5)
        
        # Check for "don't rush" message (only recent ones)
        current_time = asyncio.get_event_loop().time()
        for msg in messages:
            if msg.text and ("Будь ласка, не поспішайте" in msg.text or "не поспішайте" in msg.text):
                # Check if message is recent (within last 5 seconds)
                if msg.date and (datetime.now().timestamp() - msg.date.timestamp()) < 5:
                    self.dont_rush_count += 1
                    if self.dont_rush_count > 10:
                        logger.error("Too many 'don't rush' messages - stopping to prevent infinite loop")
                        raise Exception("Bot is being rate limited too heavily")
                    
                    logger.warning(f"Game says 'don't rush' - waiting 10 seconds and refreshing... (count: {self.dont_rush_count})")
                    await asyncio.sleep(10)
                    # Send /start to truly refresh
                    await self.send_start_command()
                    await asyncio.sleep(2)
                    # Retry navigation
                    return await self.navigate_to_inventory(0)  # Reset retry count
        
        for msg in messages:
            if msg.buttons:
                for row_idx, row in enumerate(msg.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and "Інвентар" in btn.text:
                            await self.human_delay()
                            # Fire-and-forget click to avoid API delays
                            asyncio.create_task(msg.click(row_idx, btn_idx))
                            logger.info("Clicked 'Інвентар' button")
                            await asyncio.sleep(2)  # Give more time for navigation
                            return True
        
        # Always retry - no limit
        logger.warning(f"Could not find 'Інвентар' button, retrying in 3 seconds... (attempt {retry_count + 1})")
        await asyncio.sleep(3)
        
        # Send /start to refresh if we've tried many times
        if retry_count > 0 and retry_count % 3 == 0:
            logger.info("Sending /start to refresh menu after multiple failures")
            await self.send_start_command()
        
        return await self.navigate_to_inventory(retry_count + 1)
    
    async def navigate_to_equipment(self, retry_count=0):
        """Navigate to equipment section (Спорядження) with unlimited retries"""
        logger.info(f"Navigating to equipment section... (attempt {retry_count + 1})")
        await self.human_delay()
        
        # Look for inventory menu with equipment button
        messages = await self.client.get_messages(self.game_chat, limit=5)
        
        # Check for "don't rush" message (only recent ones)
        for msg in messages:
            if msg.text and ("Будь ласка, не поспішайте" in msg.text or "не поспішайте" in msg.text):
                # Check if message is recent (within last 5 seconds)
                if msg.date and (datetime.now().timestamp() - msg.date.timestamp()) < 5:
                    logger.warning("Game says 'don't rush' - waiting 10 seconds and refreshing...")
                    await asyncio.sleep(10)
                    # Send /start to truly refresh
                    await self.send_start_command()
                    await asyncio.sleep(2)
                    # Retry navigation from start
                    return await self.navigate_to_inventory()  # Start from beginning
        
        for msg in messages:
            if msg.buttons:
                for row_idx, row in enumerate(msg.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and "Спорядження" in btn.text:
                            await self.human_delay()
                            # Fire-and-forget click to avoid API delays
                            asyncio.create_task(msg.click(row_idx, btn_idx))
                            logger.info("Clicked 'Спорядження' button")
                            await asyncio.sleep(2)  # Give more time for navigation
                            return True
        
        # Always retry - no limit
        logger.warning(f"Could not find 'Спорядження' button, retrying... (attempt {retry_count + 1})")
        
        # If we've tried a few times, we might not be in inventory menu
        if retry_count > 0 and retry_count % 2 == 0:
            logger.info("Equipment button not found after multiple attempts, going back to inventory first")
            # Navigate to inventory first
            if await self.navigate_to_inventory():
                await asyncio.sleep(2)
                # Now try equipment again
                return await self.navigate_to_equipment(0)  # Reset counter
        
        await asyncio.sleep(5)
        return await self.navigate_to_equipment(retry_count + 1)
    
    async def navigate_to_last_page(self, retry_count=0):
        """Navigate to the last inventory page using left arrow with unlimited retries"""
        logger.info(f"Navigating to last inventory page... (attempt {retry_count + 1})")
        await self.human_delay()
        
        # Look for navigation arrows and click left arrow
        messages = await self.client.get_messages(self.game_chat, limit=5)
        
        # Check for "don't rush" message (only recent ones)
        for msg in messages:
            if msg.text and ("Будь ласка, не поспішайте" in msg.text or "не поспішайте" in msg.text):
                # Check if message is recent (within last 5 seconds)
                if msg.date and (datetime.now().timestamp() - msg.date.timestamp()) < 5:
                    logger.warning("Game says 'don't rush' - waiting 10 seconds and refreshing...")
                    await asyncio.sleep(10)
                    # Send /start to truly refresh
                    await self.send_start_command()
                    await asyncio.sleep(2)
                    # Retry navigation from start
                    return await self.navigate_to_inventory()  # Start from beginning
        
        for msg in messages:
            if msg.buttons:
                for row_idx, row in enumerate(msg.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and ("⬅️" in btn.text or "←" in btn.text):
                            await self.human_delay()
                            # Fire-and-forget click to avoid API delays
                            asyncio.create_task(msg.click(row_idx, btn_idx))
                            logger.info("Clicked left arrow to go to last page")
                            await asyncio.sleep(1)
                            
                            # Store the inventory message for later use
                            await asyncio.sleep(1)  # Let page load
                            updated_messages = await self.client.get_messages(self.game_chat, limit=5)
                            for updated_msg in updated_messages:
                                if updated_msg.text and ("Сторінка" in updated_msg.text and "предметів" in updated_msg.text):
                                    self.inventory_message = updated_msg
                                    logger.info("Stored inventory message reference")
                                    break
                            return True
        
        # If no left arrow found, maybe we're already on the last page
        # Check if there are item buttons present and store the message
        for msg in messages:
            if msg.buttons and msg.text and ("Сторінка" in msg.text and "предметів" in msg.text):
                self.inventory_message = msg
                logger.info("Already on correct page, stored inventory message reference")
                return True
        
        # Always retry - no limit
        logger.warning(f"Could not find left arrow button, retrying in 5 seconds... (attempt {retry_count + 1})")
        await asyncio.sleep(5)
        return await self.navigate_to_last_page(retry_count + 1)
    
    async def find_leather_boots(self):
        """Find leather boots button on current inventory page"""
        logger.info(f"Looking for '{self.item_to_disassemble}' in inventory...")
        await asyncio.sleep(1)  # Small delay to let page load
        
        messages = await self.client.get_messages(self.game_chat, limit=3)
        
        for msg in messages:
            if msg.buttons:
                for row_idx, row in enumerate(msg.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and self.item_to_disassemble in btn.text:
                            logger.info(f"Found '{self.item_to_disassemble}' button!")
                            return msg, row_idx, btn_idx
        
        logger.info(f"No '{self.item_to_disassemble}' found on current page")
        return None, None, None
    
    async def select_item_for_disassembly(self, msg, row_idx, btn_idx):
        """Select the leather boots item for disassembly"""
        logger.info(f"Selecting '{self.item_to_disassemble}' for disassembly...")
        await self.human_delay()
        # Fire-and-forget click to avoid API delays
        asyncio.create_task(msg.click(row_idx, btn_idx))
        await asyncio.sleep(1)
        logger.info("Item selected, looking for dismantle option...")
    
    async def click_dismantle_button(self, retry_count=0):
        """Click the dismantle button (Розібрати на брухт) with unlimited retries"""
        logger.info(f"Looking for dismantle button... (attempt {retry_count + 1})")
        await self.human_delay()
        
        messages = await self.client.get_messages(self.game_chat, limit=5)
        
        # Check for "don't rush" message (only recent ones)
        for msg in messages:
            if msg.text and ("Будь ласка, не поспішайте" in msg.text or "не поспішайте" in msg.text):
                # Check if message is recent (within last 5 seconds)
                if msg.date and (datetime.now().timestamp() - msg.date.timestamp()) < 5:
                    logger.warning("Game says 'don't rush' - waiting 10 seconds...")
                    await asyncio.sleep(10)
                    # Retry the same action
                    return await self.click_dismantle_button(0)  # Reset retry count
        
        for msg in messages:
            if msg.buttons:
                for row_idx, row in enumerate(msg.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and ("Розібрати на брухт" in btn.text or "брухт" in btn.text):
                            await self.human_delay()
                            # Fire-and-forget click to avoid API delays
                            asyncio.create_task(msg.click(row_idx, btn_idx))
                            logger.info("Clicked dismantle button")
                            await asyncio.sleep(1)
                            return True
        
        # Always retry - no limit
        logger.warning(f"Could not find dismantle button, retrying in 5 seconds... (attempt {retry_count + 1})")
        await asyncio.sleep(5)
        return await self.click_dismantle_button(retry_count + 1)
    
    
    async def return_to_inventory_page(self):
        """Return to the inventory page by searching for it (no message storage)"""
        logger.info("Returning to inventory page...")
        await self.human_delay()
        
        # Check for "don't rush" message first (only recent ones)
        messages = await self.client.get_messages(self.game_chat, limit=5)
        for msg in messages:
            if msg.text and ("Будь ласка, не поспішайте" in msg.text or "не поспішайте" in msg.text):
                # Check if message is recent (within last 5 seconds)
                if msg.date and (datetime.now().timestamp() - msg.date.timestamp()) < 5:
                    logger.warning("Game says 'don't rush' - waiting 10 seconds...")
                    await asyncio.sleep(10)
                    # Send /start to get back to main menu after wait
                    await self.send_start_command()
                    return False  # Force re-navigation
        
        # Always search for inventory message in recent messages (reliable approach)
        messages = await self.client.get_messages(self.game_chat, limit=20)
        
        for msg in messages:
            if msg.text and ("Сторінка" in msg.text and "предметів" in msg.text) and msg.buttons:
                logger.info("Found inventory page message")
                
                # Click left arrow to go to last page
                for row_idx, row in enumerate(msg.buttons):
                    for btn_idx, btn in enumerate(row):
                        if btn.text and ("⬅️" in btn.text or "←" in btn.text):
                            await self.human_delay()
                            # Fire-and-forget click to avoid API delays
                            asyncio.create_task(msg.click(row_idx, btn_idx))
                            logger.info("Clicked left arrow on inventory page")
                            await asyncio.sleep(1)
                            return True
                
                # If no left arrow, we're already on the right page
                logger.info("Inventory page found, no left arrow needed")
                return True
        
        logger.warning("Could not find inventory page, trying to re-navigate...")
        return False
    
    async def start_disassembly_process(self):
        """Main disassembly process"""
        try:
            logger.info("=== DISASSEMBLY BOT STARTING ===")
            
            # Connect to game bot
            self.game_chat = await self.client.get_entity(self.config.GAME_BOT_USERNAME)
            logger.info(f"Connected to game bot: {self.game_chat.username}")
            
            # Send /start to refresh menu
            await self.send_start_command()
            
            # Navigate to inventory
            if not await self.navigate_to_inventory():
                raise Exception("Failed to navigate to inventory")
            
            # Navigate to equipment section
            if not await self.navigate_to_equipment():
                raise Exception("Failed to navigate to equipment section")
            
            # Navigate to last page
            if not await self.navigate_to_last_page():
                raise Exception("Failed to navigate to last page")
            
            # Start disassembly loop
            self.is_running = True
            consecutive_failures = 0
            max_consecutive_failures = 5  # Increased for more thorough checking
            
            while self.is_running:
                logger.info(f"Looking for items to disassemble (attempt after {consecutive_failures} failures)...")
                
                # Look for leather boots
                msg, row_idx, btn_idx = await self.find_leather_boots()
                
                if msg is None:
                    logger.info("No more leather boots found on current page")
                    consecutive_failures += 1
                    
                    if consecutive_failures < max_consecutive_failures:
                        logger.info(f"Checking again... ({consecutive_failures}/{max_consecutive_failures})")
                        await asyncio.sleep(2)
                        continue
                    else:
                        # Try complete re-navigation before giving up
                        logger.info("No items found after multiple checks, trying complete re-navigation...")
                        
                        # Send /start and navigate from beginning
                        await self.send_start_command()
                        
                        if await self.navigate_to_inventory() and await self.navigate_to_equipment() and await self.navigate_to_last_page():
                            logger.info("Re-navigation successful, doing final check...")
                            
                            # Do one final check after re-navigation
                            await asyncio.sleep(2)
                            final_msg, final_row, final_btn = await self.find_leather_boots()
                            
                            if final_msg is not None:
                                logger.info("Found items after re-navigation! Continuing...")
                                msg, row_idx, btn_idx = final_msg, final_row, final_btn
                                consecutive_failures = 0  # Reset counter
                            else:
                                logger.info("No items found even after complete re-navigation. All items processed!")
                                break
                        else:
                            logger.error("Re-navigation failed - likely all items have been processed")
                            break
                
                # Reset failure counter since we found an item
                consecutive_failures = 0
                
                # Select item for disassembly
                await self.select_item_for_disassembly(msg, row_idx, btn_idx)
                
                # Click dismantle button
                if not await self.click_dismantle_button():
                    logger.error("Failed to click dismantle button, skipping...")
                    await asyncio.sleep(1)
                    continue
                
                # Wait for confirmation dialog and click "Так"
                logger.info("Looking for confirmation dialog...")
                await asyncio.sleep(1)  # Give dialog time to appear
                
                confirmation_clicked = False
                messages = await self.client.get_messages(self.game_chat, limit=3)
                
                for msg in messages:
                    if (msg.buttons and msg.text and 
                        "впевнені" in msg.text and "розібрати" in msg.text):
                        
                        # Find and click "Так" button
                        for row_idx, row in enumerate(msg.buttons):
                            for btn_idx, btn in enumerate(row):
                                if btn.text and "Так" in btn.text:
                                    # Fire off the click without waiting for it to complete
                                    asyncio.create_task(msg.click(row_idx, btn_idx))
                                    logger.info("Clicked 'Так' confirmation button")
                                    confirmation_clicked = True
                                    break
                            if confirmation_clicked:
                                break
                        break
                
                if not confirmation_clicked:
                    logger.warning("No confirmation dialog found, continuing anyway...")
                
                # Brief wait for click to register, then continue
                await asyncio.sleep(0.5)
                                
                # Count successful disassembly
                self.items_disassembled += 1
                logger.info(f"Item disassembled! Total: {self.items_disassembled}")
                
                # Add extra delay every 10 items to avoid "don't rush" message
                if self.items_disassembled % 10 == 0:
                    logger.info("Processed 10 items, taking a 15 second break to avoid rate limiting...")
                    await asyncio.sleep(15)
                
                # Return to inventory page to look for more items
                if not await self.return_to_inventory_page():
                    logger.warning("Failed to return to inventory page, trying to re-navigate...")
                    
                    # Send /start and try to navigate from the beginning
                    logger.info("Starting complete re-navigation from /start...")
                    await self.send_start_command()
                    
                    # Try full navigation from start
                    if not await self.navigate_to_inventory():
                        logger.error("Failed to navigate to inventory from start")
                        break
                    
                    if not await self.navigate_to_equipment():
                        logger.error("Failed to navigate to equipment from start")
                        break
                    
                    if not await self.navigate_to_last_page():
                        logger.error("Failed to navigate to last page from start")
                        break
                    
                    logger.info("Successfully re-navigated from start")
                
                # No delay - immediately start next iteration
            
            # Disassembly complete
            logger.info(f"=== DISASSEMBLY COMPLETE ===")
            logger.info(f"Total items disassembled: {self.items_disassembled}")
            
            # Return to main menu
            await self.send_start_command()
            
            # Stop the process
            self.is_running = False
            logger.info("Disassembly bot finished successfully")
            
        except Exception as e:
            logger.error(f"Error in disassembly process: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the disassembly bot"""
        self.is_running = False
        logger.info("Disassembly bot stopped")


async def main():
    """Main function to run the disassembly bot"""
    config = Config()
    
    # Parse command line arguments for customization
    import argparse
    parser = argparse.ArgumentParser(description='AutoOstromag Disassembly Bot')
    parser.add_argument('--item', default='Шкіряні Чоботи', help='Item to disassemble (default: Шкіряні Чоботи)')
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
        
        # Initialize disassembly bot
        disassembly_bot = DisassemblyBot(client, config, args.item)
        
        # Start the disassembly process
        await disassembly_bot.start_disassembly_process()
        
        logger.info("Disassembly bot completed. Exiting...")
        
    except KeyboardInterrupt:
        logger.info("Disassembly bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await client.disconnect()
        logger.info("Client disconnected")
        # Exit the process entirely
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
