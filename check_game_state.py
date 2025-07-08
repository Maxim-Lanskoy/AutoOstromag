#!/usr/bin/env python3
"""
Check current game state
"""

import asyncio
from telethon import TelegramClient
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def check_state():
    config = Config()
    client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)
    
    try:
        await client.start()
        game_chat = await client.get_entity(config.GAME_BOT_USERNAME)
        
        # Send character command
        await client.send_message(game_chat, "🧍 Персонаж")
        await asyncio.sleep(2)
        
        # Get recent messages
        messages = await client.get_messages(game_chat, limit=15)
        
        logger.info("=== GAME STATE CHECK ===")
        for i, msg in enumerate(messages):
            if msg.text:
                logger.info(f"\nMessage {i}:")
                logger.info(f"Text: {msg.text[:150]}...")
                if msg.buttons:
                    logger.info("Buttons:")
                    for row_idx, row in enumerate(msg.buttons):
                        for btn_idx, btn in enumerate(row):
                            logger.info(f"  [{row_idx},{btn_idx}]: {btn.text}")
        
        # Look for specific states
        for msg in messages:
            if msg.text:
                if "Раунд" in msg.text and msg.buttons:
                    logger.info("\n⚔️ ACTIVE BATTLE DETECTED!")
                    if any("Атака" in btn.text for row in msg.buttons for btn in row):
                        logger.info("Battle is ongoing - has attack buttons")
                    else:
                        logger.info("Battle might be finished - no attack buttons")
                
                if "Ви в бою!" in msg.text:
                    logger.info("\n⚠️ IN BATTLE WARNING DETECTED!")
                
                if "який подорожує" in msg.text:
                    logger.info(f"\n👋 GREETING OPPORTUNITY: {msg.text}")
                
                if "табір" in msg.text:
                    logger.info(f"\n🏕️ CAMP DETECTED: {msg.text}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_state())