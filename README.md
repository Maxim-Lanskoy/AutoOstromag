# AutoOstromag

AutoOstromag is a clean, and efficient automated userbot for the Ukrainian Telegram RPG game "Таємниці Королівства Остромаг" (@ostromag_game_bot). The bot automatically levels up your character through exploration and combat with minimal complexity and maximum reliability.

## 🚀 What the Bot Does

The bot follows a **simple, linear flow**:

1. **Send `/start` command** - refreshes the game menu
2. **Check character profile** - gets HP, energy, and regeneration times from game
3. **Wait for full HP** if needed (uses game's actual regeneration time)
4. **Explore if energy > 0** - sends exploration command
5. **Handle discoveries**:
   - **⚔️ Battles** - fights enemies with smart actions
   - **🏕️ Camps** - automatically clicks to explore them
   - **👋 Players** - greets other players for bonuses
   - **🪤 Traps** - sets up guild traps
6. **After battle** - check profile and wait for regeneration
7. **Repeat indefinitely**

### 🥊 Battle Strategy
- **🏃 Auto-escape** from powerful mobs (configurable list)
- **🔁 Retry escape** up to 5 times if escape fails
- **💊 Use potions** if HP < 100 (survival priority)
- **⚔️ Use skills** if available (damage boost)
- **👊 Otherwise attack** (basic combat)
- **📝 Detailed defeat logs** show which mob defeated you

### 🔄 Smart Features
- **🏃 Escape system** for dangerous mobs with automatic retry
- **💉 Manual healing detection** during HP wait (checks every 30s)
- **📊 Enhanced logging** with battle separators and mob names
- **⏱️ Optimized timers** no extra waiting when HP timer expires
- **🔄 Retry mechanism** for failed profile checks
- **⏰ Real regeneration times** from game
- **🏕️ Camp & trap detection** for maximum opportunities
- **🤖 Human-like delays** to avoid detection

## ⚙️ Configuration

Only **6 essential settings** in `.env`:

```bash
# Telegram API credentials
API_ID=your_api_id_here
API_HASH=your_api_hash_here
SESSION_NAME=AutoOstromag

# Game settings
GAME_BOT_USERNAME=@ostromag_game_bot

# Human-like delays (in seconds)
HUMAN_DELAY_MIN=1.0
HUMAN_DELAY_MAX=3.0

# Debug mode
DEBUG=False
```

### 🏃 Escape Mobs Configuration

The bot automatically escapes from dangerous mobs defined in `config.py`:

```python
ESCAPE_MOBS = [
    "Великий Дикий Тур",
    "Кусак Лютого Жала", 
    "Тінь Блукача",
    "Тіньовий Яструб",
    "Давній Павук-Могильник",
    "Старший Дрантогор"
]
```

You can customize this list based on your character's strength. The bot will:
- Immediately attempt to escape when encountering these mobs
- Retry escape up to 5 times if it fails
- Only fight if all escape attempts are exhausted

## 🛠️ Installation & Setup

1. **Install Python 3.8+**

2. **Clone and install**:
   ```bash
   cd AutoOstromag
   pip install -r requirements.txt
   ```

3. **Get Telegram API credentials**:
   - Visit https://my.telegram.org
   - Create application and get `api_id` and `api_hash`

4. **Configure**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Run**:
   ```bash
   python main.py
   ```
## 📁 Project Structure

```
AutoOstromag/
├── main.py                    # Entry point
├── config.py                  # Minimal configuration (6 settings only)
├── requirements.txt           # Dependencies
├── .env.example              # Environment template
├── .env                      # Your credentials
│
├── modules/
│   ├── __init__.py
│   └── game_bot.py           # Main bot logic (~400 lines, well-commented)
│
├── utils/
│   ├── __init__.py
│   ├── logger.py             # Simple logging
│   └── parser.py             # Basic message parsing
│
├── Swift/                    # (Kept as requested)
├── ostromag_bot.py          # (Kept for other purposes)
└── REMOVED_FEATURES.md       # Documentation of what was removed
```
