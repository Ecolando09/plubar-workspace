#!/usr/bin/env python3
"""
Telegram → Discord Bridge for Weekly Wizdom
Monitors Weekly Wizdom and forwards trade signals to Discord
"""
import os
import sys
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv
import requests
import asyncio

load_dotenv()

API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# Channel configurations
CHANNELS = {
    'weekly-wizdom': {
        'telegram_name': 'Weekly Wizdom',
        'discord_channel_id': os.environ.get('DISCORD_WEEKLY_WIZDOM_CHANNEL_ID'),
        'discord_channel_name': '💬-weekly-wizdom',
        'emoji': '💬',
        'keywords': ['entry', 'exit', 'long', 'short', 'tp', 'sl', 'signal', 'buy', 'sell', 
                     'bullish', 'bearish', 'pump', 'crash', 'moon', 'rekt', 'trade', 'futures']
    },
    'wizard-of-soho': {
        'telegram_name': 'Wizard of Soho',
        'discord_channel_id': os.environ.get('DISCORD_WIZARD_OF_SOHO_CHANNEL_ID'),
        'discord_channel_name': '🧙‍♂️-wizard-of-soho',
        'emoji': '🧙‍♂️',
        'forward_all': True  # All messages from official channel
    },
    'daniels': {
        'telegram_name': 'Daniels',
        'discord_channel_id': os.environ.get('DISCORD_DANIELS_TRADES_CHANNEL_ID'),
        'discord_channel_name': '📊-daniels-trades',
        'emoji': '📊',
        'keywords': ['entry', 'exit', 'long', 'short', 'tp', 'sl', 'call', 'signal', 'buy', 'sell', 
                     'leverage', 'margin', 'futures', 'options', 'position']
    }
}

log_file = open('/tmp/telegram-bridge.log', 'a')

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    log_file.write(line + "\n")
    log_file.flush()
    print(line, flush=True)

log("=" * 70)
log("Weekly Wizdom Trading Bridge Starting")
log("=" * 70)

client = TelegramClient('auth_session', API_ID, API_HASH)


def is_important(text: str, keywords: list, forward_all: bool = False) -> bool:
    if forward_all:
        return True
    if not keywords:
        return False
    text_lower = text.lower()
    return sum(1 for k in keywords if k in text_lower) >= 2


async def find_channel(telegram_name: str):
    dialogs = await client.get_dialogs()
    for d in dialogs:
        if hasattr(d.entity, 'title') and d.entity.title == telegram_name:
            return d.entity
    return None


async def forward_to_discord(message, channel_config, sender: str):
    channel_id = channel_config['discord_channel_id']
    if not channel_id:
        return
    
    text = message.text[:1800]
    emoji = channel_config.get('emoji', '📱')
    payload = {'content': f"{emoji} **{sender}**\n{text}"}
    
    try:
        r = requests.post(
            f'https://discord.com/api/v10/channels/{channel_id}/messages',
            json=payload,
            headers={'Authorization': f'Bot {DISCORD_TOKEN}'},
            timeout=5
        )
        if r.status_code == 200:
            log(f"✓ Forwarded to {channel_config['discord_channel_name']}")
        else:
            log(f"✗ Discord error {r.status_code}")
    except Exception as e:
        log(f"✗ Discord error: {e}")


async def monitor_channel(telegram_name: str, channel_key: str):
    config = CHANNELS[channel_key]
    
    channel = await find_channel(telegram_name)
    if not channel:
        log(f"✗ Not found: {telegram_name}")
        return
    
    log(f"✓ Monitoring: {telegram_name} → {config['discord_channel_name']}")
    
    last_id = None
    
    while True:
        try:
            msgs = await client.get_messages(channel, limit=10)
            
            for m in reversed(msgs):
                if not m.text or (last_id and m.id <= last_id):
                    continue
                last_id = max(last_id or 0, m.id)
                
                if not is_important(m.text, config.get('keywords', []), config.get('forward_all', False)):
                    continue
                
                sender = "Unknown"
                if m.sender:
                    sender = m.sender.username or m.sender.first_name
                
                tag = "📢" if config.get('forward_all') else "📈"
                log(f"{tag} {sender}: {m.text[:60]}...")
                
                await forward_to_discord(m, config, sender)
            
            await asyncio.sleep(5)
            
        except Exception as e:
            log(f"Error in {telegram_name}: {e}")
            await asyncio.sleep(10)


async def main():
    await client.connect()
    
    log("Active channels:")
    for key, config in CHANNELS.items():
        channel = await find_channel(config['telegram_name'])
        if channel:
            status = "✓ Active" if config['discord_channel_id'] else "⚠️  No Discord ID"
        else:
            status = "✗ Not in dialogs"
        log(f"  {config['discord_channel_name']}: {status}")
    
    log("-" * 70)
    
    # Monitor all accessible channels
    tasks = []
    for key, config in CHANNELS.items():
        if await find_channel(config['telegram_name']):
            tasks.append(monitor_channel(config['telegram_name'], key))
    
    if tasks:
        await asyncio.gather(*tasks)
    else:
        log("No channels accessible. Check your Telegram dialogs.")
        await asyncio.sleep(60)


asyncio.run(main())
