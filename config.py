"""
Configuration file for AutoGram bot
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration"""
    
    # Telegram API credentials
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')
    SESSION_NAME = os.getenv('SESSION_NAME', 'autogram_session')
    
    # Game settings
    GAME_BOT_USERNAME = os.getenv('GAME_BOT_USERNAME', '@ostromag_game_bot')
    
    # Battle settings
    USE_SKILLS_IN_BATTLE = os.getenv('USE_SKILLS_IN_BATTLE', 'True').lower() == 'true'
    USE_POTIONS_IN_BATTLE = os.getenv('USE_POTIONS_IN_BATTLE', 'True').lower() == 'true'
    AUTO_USE_HEALING_POTIONS = os.getenv('AUTO_USE_HEALING_POTIONS', 'True').lower() == 'true'
    
    # Battle outcome tracking
    TRACK_BATTLE_OUTCOMES = os.getenv('TRACK_BATTLE_OUTCOMES', 'True').lower() == 'true'
    
    # Error recovery settings
    MAX_CONSECUTIVE_ERRORS = int(os.getenv('MAX_CONSECUTIVE_ERRORS', '5'))
    RETRY_DELAY_MULTIPLIER = float(os.getenv('RETRY_DELAY_MULTIPLIER', '2.0'))
    
    # Health management
    MAXIMUM_HEALTH_PLACEHOLDER = int(os.getenv('MAXIMUM_HEALTH_PLACEHOLDER', '275'))
    MIN_HEALTH_PERCENT_TO_EXPLORE = float(os.getenv('MIN_HEALTH_PERCENT_TO_EXPLORE', '95'))
    
    # Status check intervals (in seconds)
    ENERGY_STATUS_CHECK_INTERVAL = int(os.getenv('ENERGY_STATUS_CHECK_INTERVAL', '180'))
    HP_STATUS_CHECK_INTERVAL = int(os.getenv('HP_STATUS_CHECK_INTERVAL', '60'))
    
    # Base delay setting (all delays will use this value)
    BASE_DELAY = float(os.getenv('BASE_DELAY', '3.0'))
    
    # All timer values derived from BASE_DELAY
    BATTLE_DELAY = BASE_DELAY
    MESSAGE_WAIT_DELAY = BASE_DELAY
    BUTTON_CLICK_DELAY = BASE_DELAY
    
    # Human-like delays
    HUMAN_DELAY_MIN = BASE_DELAY
    HUMAN_DELAY_MAX = BASE_DELAY + 1.0
    
    # All specific delays use BASE_DELAY
    INITIAL_START_DELAY_MIN = BASE_DELAY
    INITIAL_START_DELAY_MAX = BASE_DELAY + 1.0
    AFTER_START_DELAY = BASE_DELAY
    AFTER_BUTTON_CLICK_DELAY = BASE_DELAY
    
    CHARACTER_STATUS_DELAY_MIN = BASE_DELAY
    CHARACTER_STATUS_DELAY_MAX = BASE_DELAY + 1.0
    AFTER_CHARACTER_STATUS_DELAY = BASE_DELAY
    
    SKILL_BUTTON_DELAY_MIN = BASE_DELAY
    SKILL_BUTTON_DELAY_MAX = BASE_DELAY + 1.0
    SKILL_WAIT_DELAY = BASE_DELAY
    SKILL_SELECT_DELAY_MIN = BASE_DELAY
    SKILL_SELECT_DELAY_MAX = BASE_DELAY + 1.0
    AFTER_SKILL_DELAY = BASE_DELAY
    
    ESCAPE_DELAY_MIN = BASE_DELAY
    ESCAPE_DELAY_MAX = BASE_DELAY + 1.0
    ATTACK_DELAY_MIN = BASE_DELAY
    ATTACK_DELAY_MAX = BASE_DELAY + 1.0
    
    NO_ACTION_DELAY = BASE_DELAY
    AFTER_BATTLE_DELAY = BASE_DELAY
    
    EXPLORE_DELAY_MIN = BASE_DELAY
    EXPLORE_DELAY_MAX = BASE_DELAY + 1.0
    EXPLORE_WAIT_DELAY = BASE_DELAY
    CAMP_CLICK_DELAY = BASE_DELAY
    GREETING_CLICK_DELAY = BASE_DELAY
    
    MAIN_LOOP_DELAY = BASE_DELAY
    
    # Special delays (keeping these separate as they need to be longer)
    ENERGY_REGEN_EXTRA_DELAY = 5.0
    ENERGY_WAIT_MAX_CHECK_INTERVAL = 60.0
    ERROR_RETRY_DELAY = 10.0
    
    # HP regeneration
    HP_REGEN_RATE_PER_MINUTE = float(os.getenv('HP_REGEN_RATE_PER_MINUTE', '0.6'))
    
    # Battle thresholds
    LOW_HP_THRESHOLD = int(os.getenv('LOW_HP_THRESHOLD', '10'))
    CRITICAL_HP_THRESHOLD = int(os.getenv('CRITICAL_HP_THRESHOLD', '5'))
    
    # Healing potion thresholds
    HEALING_POTION_HP_THRESHOLD = int(os.getenv('HEALING_POTION_HP_THRESHOLD', '50'))
    
    # Debug
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', 'True').lower() == 'true'