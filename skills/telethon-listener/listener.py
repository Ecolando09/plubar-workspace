#!/usr/bin/env python3
"""Weekly Wizdom Listener - Simple polling"""
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

TRADE_KW = ['entry', 'exit', 'long', 'short', 'tp', 'sl', 'signal', 'buy', 'sell', 'futures']
SENT_KW = ['bullish', 'bearish', 'pump', 'crash', 'moon', 'rekt', 'breakout', 'trend']

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
    
    log(f"Monitoring: {channel.title}")
    log(f"Discord: {'Yes' if DISCORD_TOKEN else 'No'}")
    log("-" * 60)
    
    last_id = None
    
    while True:
        try:
            msgs = await client.get_messages(channel, limit=10)
            
            for m in reversed(msgs):
                if not m.text or (last_id and m.id <= last_id):
                    continue
                last_id = max(last_id or 0, m.id)
                
                txt = m.text.lower()
                is_trade = sum(1 for k in TRADE_KW if k in txt) >= 2
                is_sent = sum(1 for k in SENT_KW if k in txt) >= 2
                
                if not (is_trade or is_sent):
                    continue
                
                sender = "Unknown"
                if m.sender:
                    sender = m.sender.username or m.sender.first_name
                
                tag = "📈 TRADE" if is_trade else "💬 SENTIMENT"
                log(f"{tag} | {sender}: {m.text[:70]}...")
            
            await asyncio.sleep(10)
            
        except Exception as e:
            log(f"Error: {e}")
            await asyncio.sleep(10)

asyncio.run(run())
