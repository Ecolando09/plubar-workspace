#!/bin/bash
# Quick start script for Telethon Listener

# Install dependencies
pip install -r requirements.txt

# Copy env file if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - edit it with your credentials!"
fi

# Run listener
python3 -c "
import asyncio
import sys
from telethon_listener import TelegramListener, DiscordForwarder

async def main():
    if len(sys.argv) < 2:
        print('Usage: ./start.sh <channel_id>')
        return
    
    channel = sys.argv[1]
    listener = TelegramListener()
    
    print('Connecting to Telegram...')
    await listener.connect()
    print(f'Listening to {channel}...')
    
    # Print messages to console
    async def handler(msg):
        print(f'[{msg.date}] {msg.text[:100]}')
    
    await listener.listen_to_channel(channel, handler)
    await listener.start_listening()

asyncio.run(main())
" $1
