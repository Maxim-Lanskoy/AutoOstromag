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
   - Won't explore if HP < 40
   - Tracks energy regeneration time
   - Recovers from unknown states

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
3. Test changes with `DEBUG=True` in `.env`
4. Keep delays human-like to avoid detection

---
*This bot simulates a human player grinding levels. It's intentionally simple and focused on reliability over complex features.*
