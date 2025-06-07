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
    BATTLE_DELAY = 1.0  # Delay between battle actions (seconds)
    
    # Health management
    MAXIMUM_HEALTH_PLACEHOLDER = 275  # Placeholder for maximum health, used to calculate health percentage
    MIN_HEALTH_PERCENT_TO_EXPLORE = 95  # Minimum health percentage required to safely explore
    
    # Energy settings
    ENERGY_STATUS_CHECK_INTERVAL = 180  # Check character status every N seconds during energy wait
    
    # Health settings
    HP_STATUS_CHECK_INTERVAL = 60  # Check character status every N seconds during HP wait (2 minutes)
    
    # Auto-buy settings (DISABLED)
    AUTO_BUY_ENABLED = False  # Disabled for now
    # AUTO_BUY_ITEMS = ['Плащ Мандрівника', 'Шкіряні Чоботи', 'Дерев\'яний Щит']
        
    # Delays
    BUTTON_CLICK_DELAY = 1.0  # Delay after clicking buttons
    MESSAGE_READ_DELAY = 0.5  # Delay for reading messages
    
    # Debug
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
