# AutoGram - Automated Telegram RPG Bot

AutoGram is an automated userbot for playing the Ukrainian Telegram RPG game "Таємниці Королівства Остромаг" (@ostromag_game_bot). The bot automatically explores, fights enemies, manages resources, and levels up your character with human-like behavior.

## Project Overview

This bot was developed to automate the repetitive grinding aspects of the game while maintaining realistic, human-like interaction patterns. It's built using Python and the Telethon library for Telegram API interaction.

### Current State (as of last update)

- **Version**: 1.0 (Simplified & Optimized)
- **Focus**: Automated leveling through exploration and combat
- **Status**: Fully functional with smart state management
- **Key Achievement**: Can run indefinitely without human intervention

### What the Bot Does

1. **Automatic Exploration**: Continuously explores the game world when resources permit
2. **Combat Automation**: Fights enemies by clicking attack button with human-like delays
3. **Resource Management**: 
   - Tracks HP and waits for regeneration when below 80% HP
   - Monitors energy and waits exact regeneration time
   - Tracks gold and experience gains
   - Detects and tracks energy gains from exploration
4. **Human-like Behavior**: Random delays between 0.5-2.5 seconds for all actions
5. **State Recovery**: Can start from any game state and recover from errors

### What the Bot Doesn't Do (Currently)

- Auto-buying equipment (code exists but disabled)
- Using items from inventory (framework exists)
- Crafting items
- Completing quests
- Guild/clan interactions
- PvP battles

## Features

- **Smart Initialization**: Checks character profile once at start to get real HP/energy state
- **Automatic Battle System**: Always clicks attack button (first button) in battles
- **Intelligent Energy Management**: Tracks energy usage accurately (including greetings)
- **Health Safety**: Won't explore if HP < 80% to avoid deaths
- **Manual Intervention Support**: Periodic status checks detect when you manually use potions
- **Button Detection**: Automatically clicks first button on any message with inline keyboard
- **State Recovery**: Can start from any character state and recover from errors
- **Human-like Delays**: Randomized reaction times to appear more natural
- **Efficient Timing**: Calculates exact wait times based on HP/energy needs

## Project Structure

```
AutoGram/
├── main.py                 # Entry point - initializes Telegram client and starts bot
├── config.py              # All configuration settings (delays, thresholds, credentials)
├── requirements.txt       # Python dependencies (telethon, python-dotenv, asyncio)
├── .env.example          # Template for environment variables
├── .env                  # Your actual credentials (not in git)
├── .gitignore            # Excludes sensitive files from git
├── README.md             # This comprehensive documentation
│
├── modules/              # Core bot logic modules
│   ├── __init__.py      # Makes modules a package
│   ├── game_bot.py      # Main bot controller with game loop
│   ├── battle.py        # Battle management (simplified, logic moved to game_bot)
│   ├── character.py     # Character stats management (currently unused)
│   ├── inventory.py     # Inventory management (framework ready, unused)
│   ├── exploration.py   # Exploration logic (simplified)
│   └── town.py          # Town actions like healing/shopping (heal active, shop disabled)
│
└── utils/               # Utility modules
    ├── __init__.py      # Makes utils a package
    ├── logger.py        # Logging configuration
    └── parser.py        # Game message parser (Ukrainian text parsing)
```

## File Descriptions

### Core Files

#### `main.py`
- Entry point for the application
- Creates Telegram client with API credentials
- Initializes and starts the GameBot
- Handles graceful shutdown on Ctrl+C

#### `config.py`
- Central configuration file
- Contains all adjustable parameters:
  - Telegram API credentials (loaded from .env)
  - Game bot username (@ostromag_game_bot)
  - Battle delays and thresholds
  - Energy management settings
  - Human-like behavior timings
  - Auto-buy settings (disabled)

### Modules Directory

#### `modules/game_bot.py` (Most Important File)
The heart of the bot containing:
- `__init__`: Initializes bot state (HP, energy, level, gold)
- `start()`: Connects to game, sends /start, checks initial character state
- `check_character_status()`: Parses character profile for real stats
- `main_loop()`: Core game loop that:
  - Checks if HP >= 40 (waits if not)
  - Checks energy availability (waits exact time if not)
  - Sends explore command
  - Handles various outcomes (battle, items, greetings, etc.)
- `handle_battle_simplified()`: Manages combat by clicking attack repeatedly
- `human_delay()`: Adds random delays for natural behavior

#### `modules/battle.py`
- Currently simplified - main logic moved to game_bot.py
- Framework remains for future complex battle strategies

#### `modules/character.py`
- Contains methods for checking character stats and equipment
- Currently unused (stats tracked in game_bot.py)
- Ready for future features like equipment optimization

#### `modules/inventory.py`
- Framework for inventory management
- Methods for opening inventory, listing items, using items
- Currently unused but ready for implementation

#### `modules/exploration.py`
- Simplified exploration handler
- Actual logic moved to main game loop

#### `modules/town.py`
- `go_to_town()`: Navigates to town
- `heal_character()`: Auto-heals at healer (active)
- `buy_item()`: Auto-buys equipment (commented out)

### Utils Directory

#### `utils/logger.py`
- Configures Python logging
- Outputs to console with timestamps
- Different log levels (INFO, DEBUG, ERROR)

#### `utils/parser.py`
- Parses Ukrainian game messages using regex
- Key methods:
  - `parse_character_info()`: Extracts level, HP, energy, gold
  - `parse_battle_start()`: Gets enemy stats
  - `parse_battle_round()`: Tracks HP during combat
  - `parse_battle_rewards()`: Extracts gold, XP, items
  - `parse_heal_cost()`: Calculates healing prices
  - `parse_shop_item()`: Reads shop inventory
  - `parse_inventory_item()`: Parses owned items

## Installation & Setup

1. **Install Python 3.8+**

2. **Clone/Download the project**:
   ```bash
   cd /Users/maximlanskoy/Downloads/AutoGram
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Get Telegram API credentials**:
   - Visit https://my.telegram.org
   - Login with your phone
   - Go to "API development tools"
   - Create application
   - Copy `api_id` and `api_hash`

5. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

6. **Run the bot**:
   ```bash
   python main.py
   ```

## Configuration Guide

Key settings in `config.py`:

```python
# Game bot username
GAME_BOT_USERNAME = '@ostromag_game_bot'

# Health management
MIN_HEALTH_TO_EXPLORE = 40  # Won't fight below this HP

# Battle settings
BATTLE_DELAY = 2.5  # Seconds between attack clicks

# Auto-buy (disabled)
AUTO_BUY_ENABLED = False  # Set True to enable
```

## How It Works

1. **Startup**:
   - Connects to Telegram
   - Finds game bot chat
   - Sends /start command
   - Checks character profile for initial state

2. **Main Loop**:
   - Checks HP (waits if < 40)
   - Checks energy (waits exact regen time if 0)
   - Sends explore command
   - Processes outcomes:
     - **Battle**: Clicks attack until victory/defeat
     - **No Energy**: Parses wait time, waits
     - **Found Item**: Continues exploring
     - **Met Player**: Uses energy, continues

3. **Battle System**:
   - Detects battle start
   - Finds messages with round info and buttons
   - Clicks attack with human-like delay
   - Updates HP from battle messages
   - Detects victory/defeat

4. **Resource Management**:
   - HP regenerates ~12 per 20 minutes
   - Energy shows exact wait time in messages
   - Bot calculates optimal wait periods

## Extending the Bot

### To Enable Auto-Buy:
1. Set `AUTO_BUY_ENABLED = True` in config.py
2. Uncomment `buy_item()` method in town.py
3. Add item names to `AUTO_BUY_ITEMS` list

### To Add Item Usage:
1. Implement button detection in inventory.py
2. Add item effect parsing
3. Create usage strategies (e.g., use potion when HP < 50%)

### To Add Crafting:
1. Create `modules/crafting.py`
2. Parse crafting menu and requirements
3. Implement material tracking
4. Add crafting decisions to main loop

### To Add Quest Support:
1. Create `modules/quests.py`
2. Parse quest messages
3. Track quest progress
4. Modify exploration to complete quest objectives

## Troubleshooting

1. **"Failed to get character info"**
   - Bot might be in wrong menu
   - Try deleting all messages and restarting

2. **Energy wait time incorrect**
   - Game shows time until next point
   - Bot adds 5 second buffer for safety

3. **Bot not clicking buttons**
   - Check if game interface changed
   - Verify button detection in logs

4. **High CPU usage**
   - Increase delays in config
   - Check for infinite loops in logs

## Future Improvements

- [ ] Smarter battle tactics (defend when low HP)
- [ ] Equipment management and optimization
- [ ] Automatic item usage (potions, food)
- [ ] Resource crafting system
- [ ] Quest completion
- [ ] Guild participation
- [ ] Statistics tracking
- [ ] Web dashboard
- [ ] Multi-account support

## For New Developers

To continue development:

1. **Understand current state**: Bot focuses on core leveling loop
2. **Check game_bot.py**: Contains most active logic
3. **Review parser.py**: Handles all Ukrainian text parsing
4. **Test carefully**: Game might ban for too-fast actions
5. **Keep human-like**: Always add random delays
6. **Log everything**: Helps debug game state issues

## Important Notes

- Bot operates in Ukrainian (game language)
- All text parsing uses Ukrainian patterns
- Game uses emoji extensively in messages
- Button index 0 is usually the primary action
- HP below 20% risks death in battles
- Energy regenerates 1 point per X minutes (varies by level)

## Disclaimer

This bot is for educational purposes. Use at your own risk. Ensure compliance with:
- Telegram Terms of Service
- Game rules and fair play policies
- Local laws regarding automation

The developers are not responsible for any consequences of using this bot.

---

*Last updated: Current session - Bot is working with human-like delays and smart state management*
