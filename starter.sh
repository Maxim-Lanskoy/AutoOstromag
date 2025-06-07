#!/bin/bash

# AutoOstromag Swift Bot Starter
echo "🚀 Starting AutoOstromag Swift Bot..."

# Build and run the Swift package
cd "$(dirname "$0")"

echo "📦 Building Swift package..."
swift build

if [ $? -eq 0 ]; then
    echo "✅ Build successful! Starting bot..."
    
    # Check if help is requested
    if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        swift run AutoOstromag --help
        exit 0
    fi
    
    echo "🔇 Suppressing TDLib verbose logs..."
    
    # Pass all arguments to the Swift executable
    swift run AutoOstromag "$@" 2>/dev/null
else
    echo "❌ Build failed!"
    exit 1
fi
