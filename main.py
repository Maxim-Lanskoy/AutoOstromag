#!/usr/bin/env python3
"""
AutoGram - Telegram RPG Bot for "Таємниці Королівства Остромаг"
Main entry point for the bot
"""

import asyncio
import sys
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from modules.game_bot import GameBot
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    """Main function to run the bot"""
    config = Config()
    
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
        
        # Initialize game bot
        game_bot = GameBot(client, config)
        
        # Start the bot
        await game_bot.start()
        
        # Keep the bot running
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await client.disconnect()
        logger.info("Client disconnected")


if __name__ == "__main__":
    asyncio.run(main())
