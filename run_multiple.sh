#!/bin/bash

# Example script to run multiple Ostromag bot instances
# Each instance will use its own .env file and session directory

echo "🚀 Starting Multiple Ostromag Bots..."
echo "Each bot will have its own session in TGDB_<name>/ directory"
echo ""

# Function to start a bot in a new terminal window (macOS)
start_bot_macos() {
    local env_file=$1
    local title=$2
    
    osascript <<EOF
tell application "Terminal"
    do script "cd '$PWD' && ./starter.sh --env-file '$env_file'"
    set custom title of front window to "$title"
end tell
EOF
}

# Function to start a bot in background (Linux/general)
start_bot_background() {
    local env_file=$1
    local name=$2
    
    echo "Starting $name with $env_file..."
    ./starter.sh --env-file "$env_file" > "logs_$name.txt" 2>&1 &
    echo "PID: $!"
}

# Check OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - open in new Terminal windows
    echo "📱 macOS detected - opening bots in new Terminal windows..."
    
    # Start each bot in its own terminal
    start_bot_macos ".env.shinobi" "Ostromag - Shinobi"
    sleep 2
    start_bot_macos ".env.basel" "Ostromag - B.A.S.E.L."
    sleep 2
    start_bot_macos ".env.johndoe" "Ostromag - John Doe"
    sleep 2
    start_bot_macos ".env.beehunter" "Ostromag - Bee Hunter"
    
    # Add more accounts as needed:
    # start_bot_macos ".env.account1" "Ostromag Bot - Account 1"
    
else
    # Linux/Other - run in background
    echo "🐧 Running bots in background..."
    echo "Logs will be saved to logs_<name>.txt files"
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Start bots in background
    start_bot_background ".env.shinobi" "shinobi"
    start_bot_background ".env.basel" "basel"
    start_bot_background ".env.johndoe" "johndoe"
    start_bot_background ".env.beehunter" "beehunter"
    
    # Add more accounts as needed:
    # start_bot_background ".env.account1" "account1"
    
    echo ""
    echo "✅ Bots started! Check logs_*.txt files for output"
    echo "To stop all bots: killall AutoOstromag"
fi

echo ""
echo "📂 Session directories:"
echo "  - TGDB_shinobi/     (for .env.shinobi)"
echo "  - TGDB_basel/       (for .env.basel)"
echo "  - TGDB_johndoe/     (for .env.johndoe)"
echo "  - TGDB_beehunter/   (for .env.beehunter)"
echo ""
echo "🔍 Each bot maintains its own session and can run simultaneously!"
