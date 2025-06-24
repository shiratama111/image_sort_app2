#!/bin/bash
# Railway環境を示す環境変数を設定
export RAILWAY_ENVIRONMENT=true

echo "Starting AI えびすや Bot..."
echo "Environment: Railway"
echo "Python version:"
python --version
echo "Checking environment variables..."
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "ERROR: DISCORD_BOT_TOKEN is not set!"
else
    echo "DISCORD_BOT_TOKEN is set (length: ${#DISCORD_BOT_TOKEN})"
fi
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY is not set!"
else
    echo "OPENAI_API_KEY is set (length: ${#OPENAI_API_KEY})"
fi
echo "Starting bot..."
python main.py