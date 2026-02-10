#!/usr/bin/env python3
"""Weekly Wizdom Hourly Summary"""
import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/telethon-listener')
from telethon import TelegramClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv('/root/.openclaw/workspace/skills/telethon-listener/.env')

async def main():
    client = TelegramClient('auth_session', os.environ.get('API_ID'), os.environ.get('API_HASH'))
    await client.connect()
    
    # Find channel
    dialogs = await client.get_dialogs()
    for d in dialogs:
        if hasattr(d.entity, 'title') and d.entity.title == 'Weekly Wizdom':
            channel = d.entity
            break
    
    if not channel:
        print("Channel not found!")
        await client.disconnect()
        return
    
    # Get last hour of messages
    cutoff = datetime.utcnow() - timedelta(hours=1)
    msgs = await client.get_messages(channel, limit=100)
    
    # Filter last hour
    recent = [m for m in msgs if m.date >= cutoff and m.text]
    
    print(f"📊 Weekly Wizdom - Last Hour ({len(recent)} messages)")
    print("=" * 60)
    
    trade_keywords = ['entry', 'exit', 'long', 'short', 'tp', 'sl', 'buy', 'sell', 'call', 'signal']
    trades = []
    banter = []
    
    for m in recent:
        sender = m.sender.username if m.sender and m.sender.username else (m.sender.first_name if m.sender else 'Unknown')
        text = m.text[:200]
        
        if any(kw in text.lower() for kw in trade_keywords):
            trades.append((sender, text))
        else:
            banter.append((sender, text))
    
    if trades:
        print("\n🎯 POTENTIAL TRADES:")
        for sender, text in trades[:5]:
            print(f"  @{sender}: {text}")
    else:
        print("\n⚠️ No clear trade signals detected")
    
    if banter:
        print(f"\n💬 Recent chat ({len(banter)} messages):")
        for sender, text in banter[-5:]:
            print(f"  @{sender}: {text[:80]}")
    
    await client.disconnect()

asyncio.run(main())
