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
    
    # Daily energy limit (0 = unlimited)
    DAILY_ENERGY_LIMIT = int(os.getenv('DAILY_ENERGY_LIMIT', '0'))
    
    # Exploration time window (-1 = always explore, 0-23 = start hour)
    EXPLORATION_START_HOUR = int(os.getenv('EXPLORATION_START_HOUR', '-1'))
    
    # Human-like behavior level (0-5, where 0 is disabled and 5 is maximum human-like)
    HUMAN_LIKE = int(os.getenv('HUMAN_LIKE', '0'))
    
    # Escape configuration - mobs to immediately run away from
    ESCAPE_MOBS = [
        "Великий Дикий Тур",
        "Кусак Лютого Жала",
        "Тінь Блукача",
        "Тіньовий Яструб",
        "Давній Павук-Могильник",
        "Старший Дрантогор",
        "Лютий Злоніч"
    ]
