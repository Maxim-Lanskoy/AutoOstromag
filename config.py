"""
Configuration file for AutoGram bot
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration"""
    
    # Telegram API credentials
    API_ID = int(os.getenv('API_ID', ''))
    API_HASH = os.getenv('API_HASH', '')
    SESSION_NAME = os.getenv('SESSION_NAME', 'autogram_session')
    
    # Game settings
    GAME_BOT_USERNAME = '@ostromag_game_bot'  # The game bot username
    
    # Battle settings
    BATTLE_DELAY = 2.5  # Delay between battle actions (seconds)
    MIN_HEALTH_PERCENT = 20  # Minimum health percentage before healing
    MIN_HEALTH_TO_EXPLORE = 100  # Changed from 40 to 100 - won't start battles below this HP  # Minimum HP required to safely explore
    
    # Energy settings
    ENERGY_CHECK_INTERVAL = 60  # Check energy every N seconds
    MIN_ENERGY_TO_EXPLORE = 1  # Minimum energy required to explore
    
    # Auto-buy settings (DISABLED)
    AUTO_BUY_ENABLED = False  # Disabled for now
    # AUTO_BUY_ITEMS = ['Плащ Мандрівника', 'Шкіряні Чоботи', 'Дерев\'яний Щит']
    
    # Auto-heal settings
    AUTO_HEAL_ENABLED = True
    HEAL_THRESHOLD = 30  # Heal when health is below this percentage
    
    # Delays
    BUTTON_CLICK_DELAY = 1.0  # Delay after clicking buttons
    MESSAGE_READ_DELAY = 0.5  # Delay for reading messages
    
    # Human-like behavior
    HUMAN_DELAY_MIN = 0.5  # Minimum human reaction time (seconds)
    HUMAN_DELAY_MAX = 2.0  # Maximum human reaction time (seconds)
    BATTLE_THINK_MIN = 1.0  # Minimum thinking time in battles
    BATTLE_THINK_MAX = 2.5  # Maximum thinking time in battles
    
    # Debug
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
