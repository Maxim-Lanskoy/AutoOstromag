"""
Simplified Configuration for AutoOstromag bot
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration"""
    
    # Telegram API credentials
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')
    SESSION_NAME = os.getenv('SESSION_NAME', 'AutoOstromag')
    
    # Game settings
    GAME_BOT_USERNAME = os.getenv('GAME_BOT_USERNAME', '@ostromag_game_bot')
    
    # Human-like delays
    HUMAN_DELAY_MIN = float(os.getenv('HUMAN_DELAY_MIN', '1.0'))
    HUMAN_DELAY_MAX = float(os.getenv('HUMAN_DELAY_MAX', '3.0'))
    
    # Debug
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Escape configuration - mobs to immediately run away from
    ESCAPE_MOBS = [
        "Великий Дикий Тур",
        "Кусак Лютого Жала",
        "Тінь Блукача",
        "Тіньовий Яструб",
        "Давній Павук-Могильник",
        "Старший Дрантогор"
    ]
