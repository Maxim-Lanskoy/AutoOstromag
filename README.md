# AutoOstromag

AutoOstromag is a clean, and efficient automated userbot for the Ukrainian Telegram RPG game "Таємниці Королівства Остромаг" (@ostromag_game_bot). The bot automatically levels up your character through exploration and combat with minimal complexity and maximum reliability.

## 🔔 Recent Changes

- **Raid Window Override:** On Tue/Thu/Sun between `20:00–22:00`, exploration is always allowed regardless of `EXPLORATION_START_HOUR` and `DAILY_ENERGY_LIMIT`. The energy counter increments only up to the daily limit; beyond that, the bot keeps spending energy without incrementing the counter.
- **Pre-/Post-raid Behavior:**
  - Before 20:00 on raid days, the bot follows your normal configuration. If your configured working window is active (e.g., `EXPLORATION_START_HOUR=15`), it explores with limits as usual.
  - After 22:00 on raid days, efficient mode is enforced (prevents human-like mode). The bot continues only if your configured working window is active; otherwise it waits. If `EXPLORATION_START_HOUR=-1` (always explore), it continues after 22:00.
- **Daytime Energy Bias (12:00–19:00):** Subtle, randomized bias that sometimes nudges sessions to spend all currently available energy between human-like pauses. Keeps existing human-like flow, just a higher chance to fully deplete energy during the day.
- **HUMAN_LIKE Rebalance:**
  - Old level 3 → new level 4 (same intensity as before).
  - New level 3 inserted between old 2 and 3 (balanced).
  - Old level 5 removed; new level 5 corresponds to previous level 4 intensity.
  - Delay multipliers, reading speeds, fatigue thresholds, and full-energy wait chances updated accordingly.
- **Env Templates Synced:** `.env.example` comments updated to reflect the new HUMAN_LIKE scale. Your `.env` values remain unchanged.

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
- **📉 Daily energy limits** with 12:00 reset and persistence
- **🌙 Exploration time windows** for overnight/scheduled automation
- **🔄 Retry mechanism** for failed profile checks
- **⏰ Real regeneration times** from game
- **🏕️ Camp & trap detection** for maximum opportunities
- **🤖 Human-like delays** to avoid detection

## ⚙️ Configuration

Only **8 essential settings** in `.env`:

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

# Daily energy limit (0 = unlimited)
DAILY_ENERGY_LIMIT=0

# Exploration time window (-1 = always explore, 0-23 = start hour)
EXPLORATION_START_HOUR=-1

# Human-like behavior (0-5; rebalanced levels)
# 0 = Disabled | 1 = Minimal | 2 = Light | 3 = Balanced | 4 = Realistic (old 3) | 5 = Heavy (old 4)
HUMAN_LIKE=0
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

### ⚡ Daily Energy Limit & Time Windows

Control when and how much the bot explores:

**Energy Limits (`DAILY_ENERGY_LIMIT`)**:
- `0` = unlimited (default)
- `10` = max 10 explorations per day
- Resets daily at 12:00 (noon)
- Tracks usage in `energy_data.json`

**Time Windows (`EXPLORATION_START_HOUR`)**:
- `-1` = always explore (default)
- `23` = only explore 23:00-12:00 (overnight)
- `6` = only explore 06:00-12:00 (morning)
- Handles midnight crossover correctly

**Combined Logic**:
1. Bot waits for exploration window to open
2. Uses energy within daily limit
3. When limit reached, waits for 12:00 reset
4. After reset, waits for next exploration window
5. Raid days (Tue/Thu/Sun): 20:00–22:00 always allowed (ignores window + limit). Counter increments up to the limit; post‑22:00 normal rules apply again (unless `EXPLORATION_START_HOUR=-1`, which continues).

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
├── buying_bot.py            # Specialized bot for purchasing items from shop
├── disassembly_bot.py       # Specialized bot for disassembling items into materials
├── Swift/                    # (Kept as requested)
├── ostromag_bot.py          # (Kept for other purposes)
└── REMOVED_FEATURES.md       # Documentation of what was removed
```

## 🛒 Specialized Utility Bots

### **Buying Bot** (`buying_bot.py`)
Automated resource purchasing bot that efficiently buys items from the game shop.

**Features:**
- 🚀 **Ultra-fast purchasing** - ~3-4 seconds per item
- 🎯 **Smart navigation** - Direct path: /start → Town → Shop → Buy Items → Select → Purchase
- 🔄 **Continuous buying** - Stays on same message, clicks buy button repeatedly  
- 💰 **Configurable quantity** - Set how many items to buy (default: 100)
- 🛡️ **Reliable operation** - No message reference issues, works for unlimited purchases
- 📊 **Progress tracking** - Shows purchase count and remaining gold

**Usage:**
```bash
python buying_bot.py                           # Buy 100 leather boots (default)
python buying_bot.py --quantity 50            # Buy 50 items
python buying_bot.py --item "Other Item"      # Buy different item type
```

**Flow:** /start → 🏘️ Town → 🏪 Shop → Buy Items → Select Item → Click Buy repeatedly → /start → Exit

### **Disassembly Bot** (`disassembly_bot.py`)  
Automated crafting materials bot that disassembles items into useful resources.

**Features:**
- ⚡ **Lightning-fast processing** - ~3-4 seconds per item  
- 🎯 **Smart inventory navigation** - /start → Inventory → Equipment → Last Page → Find Items
- 🔄 **Continuous disassembly** - Processes all items automatically until none remain
- 🚀 **Fire-and-forget clicking** - No API delays, instant confirmation clicking
- 🔧 **Auto-confirmation** - Handles "Так/Ні" dialogs instantly without waiting  
- 📊 **Progress tracking** - Shows total items disassembled

**Usage:**
```bash
python disassembly_bot.py                     # Disassemble all leather boots (default)  
python disassembly_bot.py --item "Other Item" # Disassemble different item type
```

**Flow:** /start → 🎒 Inventory → ⚔️ Equipment → ⬅️ Last Page → Find Items → Dismantle → Confirm → Repeat → /start → Exit

### **Combined Workflow**
Perfect for resource management and crafting material generation:

1. **Buy resources**: `python buying_bot.py` 
2. **Convert to materials**: `python disassembly_bot.py`
