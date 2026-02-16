#!/usr/bin/env python3
"""Weekly Wizdom Listener - Analysts/Admins Only"""
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
DISCORD_CHANNEL = os.environ.get('DISCORD_CHANNEL_ID')

# Known analysts and admins - UPDATE THIS LIST
ANALYSTS_ADMINS = {
    'wizardofsoho',      # Wizard of soho
    'derivativesmonkey',  # Derivatives Monkey
    'pidgeonn',           # Pidgeonn
    'cryptofox6969',      # CryptoFox
    'daniel4sol',         # Daniel
}

# Also check display names (lowercase, no spaces for matching)
ANALYST_DISPLAY_NAMES = {
    'wizard of soho',
    'derivatives monkey',
    'pidgeonn',
    'cryptofox',
    'daniel',
}

log_file = open('/tmp/wizdom.log', 'a')

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    log_file.write(line + "\n")
    log_file.flush()
    print(line, flush=True)

log("=" * 60)
log("Weekly Wizdom Listener Starting")
log("=" * 60)
log(f"Monitoring: Analysts/Admins only")
log(f"Known analysts/admins: {', '.join(ANALYSTS_ADMINS) if ANALYSTS_ADMINS else 'NONE - UPDATE LIST'}")
log("-" * 60)

client = TelegramClient('auth_session', API_ID, API_HASH)

async def run():
    await client.connect()
    
    # Find channel
    channel = None
    dialogs = await client.get_dialogs()
    for d in dialogs:
        if hasattr(d.entity, 'title') and d.entity.title == 'Weekly Wizdom':
            channel = d.entity
            break
    
    if not channel:
        log("ERROR: Weekly Wizdom not found!")
        return
    
    log(f"Channel: {channel.title}")
    log(f"Discord: {'Yes' if DISCORD_TOKEN else 'No'}")
    
    last_id = None
    
    while True:
        try:
            msgs = await client.get_messages(channel, limit=10)
            
            for m in reversed(msgs):
                if not m.text or (last_id and m.id <= last_id):
                    continue
                last_id = max(last_id or 0, m.id)
                
                # Get sender
                sender = None
                sender_name = None
                if m.sender:
                    sender = m.sender.username or ""
                    sender_name = m.sender.first_name or ""
                
                # Check username and display name
                sender_lower = sender.lower().replace('@', '') if sender else ""
                sender_name_lower = sender_name.lower() if sender_name else ""
                
                is_analyst = (
                    sender_lower in ANALYSTS_ADMINS or 
                    sender_name_lower in ANALYST_DISPLAY_NAMES
                )
                
                if not is_analyst:
                    continue
                
                log(f"✅ FORWARDED | {sender}: {m.text[:50]}...")
            
            await asyncio.sleep(10)
            
        except Exception as e:
            log(f"Error: {e}")
            await asyncio.sleep(10)

asyncio.run(run())
