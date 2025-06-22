# Running AutoOstromag from Xcode

## Method 1: Using External Build Tool (Recommended)

1. **Open Xcode**
2. **Create a new External Build System project**:
   - File → New → Project
   - Choose "External Build System" under "Other"
   - Name it "AutoOstromag Runner"

3. **Configure the External Build Tool**:
   - Build Tool: `/bin/bash`
   - Arguments: `starter.sh --env-file .env.beehunter`
   - Directory: Set to your AutoOstromag project path

4. **Run**: Just hit the Run button in Xcode

This will run your bot with properly suppressed TDLib logs.

## Method 2: Using Custom Executable

1. **Build the project first**:
   ```bash
   swift build
   ```

2. **In Xcode**:
   - Product → Scheme → Edit Scheme
   - Under "Run", go to "Info" tab
   - Change "Executable" to "Other..."
   - Navigate to `.build/debug/AutoOstromag`

3. **Add arguments**:
   - In "Arguments" tab, add: `--env-file .env.beehunter`

4. **Suppress logs** (partial solution):
   - In "Arguments" tab, add environment variable:
   - Name: `TDLIB_LOG_VERBOSITY_LEVEL`
   - Value: `2`

## Method 3: Using the Wrapper Script

1. **Make the xcode_runner.sh executable**:
   ```bash
   chmod +x xcode_runner.sh
   ```

2. **In Xcode External Build System**:
   - Build Tool: `/path/to/AutoOstromag/xcode_runner.sh`
   - Arguments: `--env-file .env.beehunter`

## Method 4: Direct Terminal in Xcode

1. Open Terminal inside Xcode:
   - View → Debug Area → Activate Console
   - Click the "Terminal" tab (if available in your Xcode version)

2. Run directly:
   ```bash
   ./starter.sh --env-file .env.beehunter
   ```

## Method 5: Using Swift Package Manager in Xcode

1. **Open Package.swift directly in Xcode**
2. **Edit the scheme**:
   - Select "AutoOstromag" scheme
   - Edit Scheme → Run → Arguments
   - Add: `--env-file .env.beehunter`

3. **For log suppression**, add pre-action script:
   - Edit Scheme → Run → Pre-actions
   - Add "Run Script"
   - Script: `export TDLIB_VERBOSITY=2`

## Best Practice

The cleanest solution is to use Method 1 (External Build System) with your existing `starter.sh` script, as it properly handles log suppression with `2>/dev/null`.

## Quick Debug Tip

If you just want to see your bot's output without TDLib spam during development, you can filter the console output in Xcode:
- In the console area, use the filter box
- Type: `🚀` or `📨` or any of your emoji prefixes
- This will show only your bot's messages

## Environment Variables

You can also set these in Xcode's scheme editor:
- `API_ID`: Your Telegram API ID
- `API_HASH`: Your Telegram API Hash
- `PHONE_NUMBER`: Your phone number

This way you don't need the .env file when running from Xcode.
