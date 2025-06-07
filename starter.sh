#!/bin/bash

# AutoOstromag Swift Bot Starter
echo "🚀 Starting AutoOstromag Swift Bot..."

# Build and run the Swift package
cd "$(dirname "$0")"

echo "📦 Building Swift package..."
swift build

if [ $? -eq 0 ]; then
    echo "✅ Build successful! Starting bot..."
    echo "🔇 Suppressing TDLib verbose logs..."
    swift run 2>/dev/null
else
    echo "❌ Build failed!"
    exit 1
fi
