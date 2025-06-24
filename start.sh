#!/bin/bash
# Railway環境を示す環境変数を設定
export RAILWAY_ENVIRONMENT=true

echo "==================================="
echo "Starting AI えびすや Bot..."
echo "Environment: Railway"
echo "==================================="
echo "Python version:"
python --version
echo ""
echo "Environment Variables Check:"
echo "---------------------------"
echo "All environment variables:"
env | grep -E "DISCORD|OPENAI" | sed 's/=.*$/=<hidden>/'
echo ""
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "ERROR: DISCORD_BOT_TOKEN is not set!"
    echo "Available Discord-related vars:"
    env | grep -i discord
else
    echo "✓ DISCORD_BOT_TOKEN is set (length: ${#DISCORD_BOT_TOKEN})"
fi
echo ""
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY is not set!"
else
    echo "✓ OPENAI_API_KEY is set (length: ${#OPENAI_API_KEY})"
fi
echo ""
echo "Starting bot..."
echo "==================================="
python main.py