# Auto-Ostromag Swift Bot

A Swift-based Telegram userbot for automating the "Таємниці Королівства Остромаг" game using TDLibKit.

## Features

- ✅ **Smart Game Automation**: Detects game states and responds appropriately
- ⚔️ **Auto-Battle**: Automatically handles combat (battles are auto-resolved by the game)
- ⚡ **Energy Management**: Waits when energy is low (5-minute breaks)
- 🎯 **Event Detection**: Handles exploration events, item findings, and player greetings
- 📱 **TDLibKit Integration**: Native Telegram API access
- 🔄 **Continuous Operation**: Runs indefinitely with proper error handling

## Prerequisites

- macOS 14.0+
- Swift 6.1+
- Telegram account with API credentials (API ID and API Hash)

## Getting Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Copy your `api_id` and `api_hash`

## Setup & Usage

1. **Build the project:**
```bash
swift build
```

2. **Run the bot:**
```bash
# Default (uses .env in current directory)
./starter.sh

# With custom .env file
./starter.sh --env-file /path/to/your/.env

# Show help
./starter.sh --help
```

3. **Follow the prompts:**
   - Enter your Telegram API ID
   - Enter your Telegram API Hash  
   - Enter your phone number (with country code, e.g., +1234567890)
   - Enter verification code from Telegram
   - Enter 2FA password when prompted (if you have 2FA enabled)

## Managing Multiple Accounts

### Command Line Options

The bot supports custom .env files via command line arguments, making it easy to manage multiple accounts:

```bash
# Show all available options
swift run AutoOstromag --help

# Use a custom .env file
swift run AutoOstromag --env-file /path/to/custom.env

# Combine options
swift run AutoOstromag --env-file .env.account2
```

### Running Multiple Accounts

1. **Create separate .env files for each account:**
   ```bash
   .env.account1    # First account credentials
   .env.account2    # Second account credentials  
   .env.beehunter   # Special configuration
   ```

2. **Run different accounts:**
   ```bash
   # Account 1
   ./starter.sh --env-file .env.account1
   
   # Account 2 (in another terminal)
   ./starter.sh --env-file .env.account2
   
   # Using the existing .env.beehunter
   ./starter.sh --env-file .env.beehunter
   
   # Or use the helper script to run multiple bots at once (macOS)
   ./run_multiple.sh
   ```

### .env File Format

Each .env file should contain:
```
API_ID=your_api_id
API_HASH=your_api_hash
PHONE_NUMBER=+1234567890
```

### Session Management

The bot automatically creates separate session directories for each account based on the .env file name:
- `.env` → `TGDB_default/`
- `.env.beehunter` → `TGDB_beehunter/`
- `.env.account1` → `TGDB_account1/`
- `custom-config.env` → `TGDB_custom-config/`

This ensures that each account maintains its own session and doesn't interfere with others

### Tips

- If no `--env-file` is specified, the bot looks for `.env` in the current directory
- If the .env file is not found, you'll be prompted to enter credentials manually
- The bot will create session files that persist authentication between runs

## How It Works

The bot monitors messages from the "Таємниці Королівства Остромаг" chat and automatically:

### 🎮 Game Logic
- **Energy Check**: Waits 5 minutes when energy is depleted
- **Monster Battles**: Detects monsters and lets auto-combat resolve
- **Exploration Events**: Continues exploring after finding items/events
- **Victory**: Automatically continues exploring after winning battles
- **Default Action**: Starts exploration when no specific condition is met

### 📝 Detected Patterns
- `❌ Недостатньо енергії!` - Energy depletion (waits 5 minutes)
- `З'явився 🐗🐍🐺🦂` - Monster encounters (lets game handle)
- `--- Раунд` - Battle rounds in progress  
- `Ви отримали:` - Battle victory (continues exploring)
- `🕯️🐝🔍📖🗿🤝🗺️` - Exploration events (continues exploring)
- `👋 привітав` - Player greetings (ignores)

## Code Structure

- `Swift/Ostromag.swift` - Main bot implementation with TDLibKit
- `Package.swift` - Swift package configuration  
- `starter.sh` - Build and run script
- `run_multiple.sh` - Helper script to run multiple bot instances
- `README.md` - This documentation
- `DEVELOPMENT_SUMMARY.md` - Development history and technical details

## Automation Flow

```
🚀 Start Bot
    ↓
⚙️ Setup TDLib + Authenticate  
    ↓
👂 Listen to Game Chat
    ↓
📨 Message Received
    ↓
🧠 Process Game State:
    ├── ⚡ No Energy? → Wait 5 min
    ├── ⚔️ Monster? → Let game handle  
    ├── 🏆 Victory? → Continue exploring
    ├── 🎯 Event? → Continue exploring
    └── 🗺️ Default → Start exploring
```

## Technical Details

- **TDLibKit**: Native Swift wrapper for Telegram's TDLib
- **Concurrency**: Modern async/await pattern with proper error handling
- **Authentication**: Complete TDLib authentication flow
- **Message Processing**: Static methods to avoid concurrency issues
- **Game State Detection**: Pattern matching on Ukrainian game text
- **Timing**: Smart delays (2s normal, 5min for energy, 1s for events)

## Safety Features

- ✅ Only responds to the specific game chat
- ✅ Intelligent timing to avoid spam
- ✅ Energy awareness prevents wasteful actions
- ✅ Battle detection lets the game's auto-combat handle fights
- ✅ Comprehensive logging for monitoring
- ✅ Graceful error handling and recovery

## Troubleshooting

**Authentication issues**: The bot now properly handles all auth states including 2FA

**Password prompt**: If you have 2FA enabled, you'll see "🔒 2FA required. Enter your password:" prompt

**Messages not being processed**: Check that the chat title is exactly "Таємниці Королівства Остромаг"

**Build warnings**: The macOS version warnings are normal and don't affect functionality

**Energy management**: The bot automatically waits 5 minutes when energy is depleted

**TDLib logs**: The verbose TDLib logs in terminal are normal during initial setup

## Notes

- The bot is designed for continuous, autonomous operation
- It handles the exploration gameplay loop efficiently  
- Battle system is automatic in the game - bot just needs to trigger exploration
- Energy management prevents infinite clicking when depleted
- All actions are logged for monitoring and debugging
