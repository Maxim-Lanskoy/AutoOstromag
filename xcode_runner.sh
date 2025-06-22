#!/bin/bash

# Xcode Runner Script for AutoOstromag
# This script suppresses TDLib logs when running from Xcode

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to project directory
cd "$DIR"

# Build the project if needed (Xcode usually handles this)
if [ ! -d ".build" ]; then
    echo "📦 Building Swift package..."
    swift build
fi

# Run with suppressed stderr (TDLib logs)
# Pass all arguments
echo "🔇 Running with suppressed TDLib logs..."
.build/debug/AutoOstromag "$@" 2>/dev/null
