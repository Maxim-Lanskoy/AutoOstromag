# AutoGram Development Summary

## Quick Context for New Claude Instance

This is an automated Telegram userbot for the Ukrainian RPG game "Таємниці Королівства Остромаг". The bot has been developed iteratively to automate grinding/leveling.

### Current Implementation Status

**Working Features:**
- ✅ Automatic exploration and combat
- ✅ HP/energy tracking with smart waiting
- ✅ Human-like random delays (0.5-2.5 seconds)
- ✅ Character state management
- ✅ Battle automation (always attacks)
- ✅ Error recovery and state detection

**Disabled/Unfinished Features:**
- ❌ Auto-buying equipment (code exists but disabled)
- ❌ Inventory item usage
- ❌ Crafting system
- ❌ Quest completion
- ❌ Guild features

### Key Technical Details

1. **Language**: Python 3.8+ with Telethon library
2. **Game Language**: Ukrainian (all parsing is for Ukrainian text)
3. **Main Logic**: `modules/game_bot.py` contains core loop
4. **Parser**: `utils/parser.py` handles Ukrainian message parsing
5. **Config**: `config.py` has all adjustable parameters

### Recent Changes (This Session)

1. **Fixed Multiple Issues**:
   - Double /start command problem
   - Incorrect energy wait time calculations
   - Added character status check at startup
   - Better energy tracking (including greeting costs)

2. **Added Human-like Behavior**:
   - Random delays before all actions
   - Longer thinking time in battles
   - Varies between 0.5-2.5 seconds

3. **Safety Improvements**:
   - Won't explore if HP < 90% of max HP
   - Tracks energy regeneration time
   - Recovers from unknown states

### Latest Update (Fixed Battle Detection)

1. **Reverted to Working Version**:
   - Restored original battle detection logic that was working
   - Fixed battle state handling to properly find round messages
   - Added enemy flee detection ("занудьгував і втік")

2. **Health Safety Improvements**:
   - Changed from fixed HP threshold to percentage-based (90% HP required)
   - Properly calculates wait time based on actual HP regeneration rate
   - Works with any max HP value (250, 300, etc.)

3. **Energy Tracking Enhanced**:
   - Detects energy gains from exploration (+2 ⚡ енергія)
   - Better parsing of energy from messages
   - Continues to track energy usage from greetings
   - **NEW**: Periodic status checks during wait times to detect manual potion usage
   - **NEW**: Bot will immediately continue if you manually restore HP/energy with potions

### Code Architecture

```
Main Loop (game_bot.py):
1. Check resources (HP/energy)
2. Wait if needed (exact times)
3. Send explore command
4. Handle outcome:
   - Battle → Click attack until done
   - No energy → Parse wait time
   - Other → Continue exploring
```

### Known Issues/Limitations

1. **Button Detection**: Always clicks first button (index 0)
2. **No Strategy**: Only attacks in battle, no defend/run
3. **Resource Waste**: Doesn't use items or optimize equipment
4. **Single Account**: No multi-account support

### Next Development Steps

1. **Enable Auto-Buy**: Uncomment code in `town.py`
2. **Item Usage**: Implement potion/food consumption
3. **Smart Combat**: Add defend when HP low
4. **Statistics**: Track XP/hour, gold earned, etc.

### Testing Notes

- Game has anti-bot detection (needs human delays)
- Test with small changes first
- Monitor for "Будь ласка, не поспішайте" (rate limit)
- HP regenerates ~0.6 per minute
- Energy shows exact wait time in messages

### Quick Start for Development

1. Check `README.md` for full documentation
2. Review `modules/game_bot.py` for main logic
3. Keep delays human-like to avoid detection

---
*This bot simulates a human player grinding levels. It's intentionally simple and focused on reliability over complex features.*

## Swift Migration (Latest)

### Major Architecture Change

The bot has been completely rewritten from Python/Telethon to Swift/TDLibKit:

1. **New Implementation**:
- Swift-based using TDLibKit (native Telegram API)
- Modern async/await concurrency
- Simple GameState actor for thread-safe state management
- Improved authentication flow with 2FA support

2. **Command Line Arguments** (NEW):
- Added ArgumentParser for flexible configuration
- `--env-file` option to specify custom .env files
- `--help` for usage information
- Supports multiple accounts with different .env files

3. **Usage Examples**:
```bash
# Default .env
./starter.sh

# Custom .env file
./starter.sh --env-file .env.beehunter

./starter.sh --env-file .env.account2
```

4. **Key Files**:
- `Swift/Ostromag.swift` - Main bot implementation
- `Swift/GameState.swift` - Simple actor for game state
- `Swift/Handlers.swift` - Message processing logic
   - `Package.swift` - Dependencies (TDLibKit, SwiftDotenv, ArgumentParser)  
   - `starter.sh` - Build and run script with argument passthrough

5. **Session Management**:
- Sessions stored in separate directories for each account:
- `.env` uses `TGDB_default/`
  - `.env.beehunter` uses `TGDB_beehunter/`
  - Each account has its own session, preventing conflicts
   - Persistent authentication between runs
   - Debug mode shows which session directory is being used

### Game State Architecture (Simplified)

**Pure Swift Concurrency Approach**:
- Each `OstromagBot` instance has its own `GameState` actor
- No NSLock, no complex managers, just a simple actor
- Tracks only essential data: health, energy, level, battle state
- Updates are passed through closure captures (no global state)
- Thread-safe by design using Swift's actor model
