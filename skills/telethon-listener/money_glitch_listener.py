#!/usr/bin/env python3
"""
Money Glitch / Weekly Wizdom Listener
Monitors Telegram channel and forwards important messages to Discord
"""
import asyncio
import os
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv
import requests

load_dotenv()

# Configuration
TELEGRAM_API_ID = os.environ.get('API_ID')
TELEGRAM_API_HASH = os.environ.get('API_HASH')
TELEGRAM_PHONE = os.environ.get('PHONE')

DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = os.environ.get('DISCORD_CHANNEL_ID')

# Keywords for filtering
TRADE_KEYWORDS = [
    'entry', 'exit', 'long', 'short', 'leverage', 'tp', 'sl', 'stop loss',
    'take profit', 'position', 'trade', 'signal', 'buy', 'sell', 'call',
    'put', 'swing', 'scalp', 'futures', 'spot', 'margin', 'liquidation'
]

SENTIMENT_KEYWORDS = [
    'bullish', 'bearish', 'up', 'down', 'crash', 'pump', 'moon', 'rekt',
    'reversal', 'breakout', 'breakdown', 'support', 'resistance', 'trend'
]


class WeeklyWizdomListener:
    def __init__(self):
        self.client = None
        self.channel_entity = None
        self.running = False
    
    async def connect(self):
        """Connect to Telegram"""
        self.client = TelegramClient('auth_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await self.client.connect()
        print(f"✓ Connected to Telegram")
    
    async def find_channel(self):
        """Find Weekly Wizdom in dialogs"""
        dialogs = await self.client.get_dialogs()
        for d in dialogs:
            if hasattr(d.entity, 'title') and d.entity.title == 'Weekly Wizdom':
                self.channel_entity = d.entity
                return d.entity
        raise ValueError("Weekly Wizdom not found")
    
    def is_important(self, message) -> tuple[bool, str]:
        """Check if message is important"""
        if not message.text:
            return False, ""
        
        text_lower = message.text.lower()
        
        # Check for trades
        trade_count = sum(1 for kw in TRADE_KEYWORDS if kw in text_lower)
        if trade_count >= 2:
            return True, "trade"
        
        # Check for sentiment
        sentiment_count = sum(1 for kw in SENTIMENT_KEYWORDS if kw in text_lower)
        if sentiment_count >= 2:
            return True, "sentiment"
        
        return False, ""
    
    async def handle_message(self, event):
        """Handle incoming message"""
        message = event.message
        
        is_important, reason = self.is_important(message)
        
        if is_important:
            sender = "Unknown"
            if message.sender:
                sender = message.sender.username or message.sender.first_name
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{reason.upper()}] {sender}: {message.text[:60]}...")
            
            if DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID:
                await self.forward_to_discord(message, reason, sender)
    
    async def forward_to_discord(self, message, reason, sender):
        """Forward to Discord"""
        emoji = {"trade": "📈", "sentiment": "💬"}.get(reason, "📱")
        text = message.text[:1800]
        
        payload = {'content': f"{emoji} **{sender}** ({reason})\n{text}"}
        
        try:
            r = requests.post(
                f'https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages',
                json=payload,
                headers={'Authorization': f'Bot {DISCORD_BOT_TOKEN}'},
                timeout=5
            )
            if r.status_code == 200:
                print(f"  ✓ Sent to Discord")
        except Exception as e:
            print(f"  ✗ Discord error: {e}")
    
    async def start(self):
        """Start listening"""
        await self.connect()
        channel = await self.find_channel()
        
        print(f"✓ Monitoring: {channel.title}")
        print("✓ Waiting for messages (Ctrl+C to stop)...")
        
        self.running = True
        
        # Use a loop to catch messages
        async for event in self.client.iter_messages(channel, limit=None, wait_time=1):
            if not self.running:
                break
            if event.text:
                is_important, reason = self.is_important(event)
                if is_important:
                    sender = "Unknown"
                    if event.sender:
                        sender = event.sender.username or event.sender.first_name
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{reason.upper()}] {sender}: {event.text[:60]}...")
        
        await self.client.disconnect()
    
    def stop(self):
        """Stop listening"""
        self.running = False


async def main():
    print("=" * 60)
    print("Weekly Wizdom / Money Glitch Listener")
    print("=" * 60)
    
    if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN == 'your_discord_bot_token':
        print("⚠️  Messages will print to console only")
        print("   Set DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID in .env to forward")
    
    listener = WeeklyWizdomListener()
    
    try:
        await listener.start()
    except KeyboardInterrupt:
        print("\n✓ Stopped")


if __name__ == '__main__':
    asyncio.run(main())
