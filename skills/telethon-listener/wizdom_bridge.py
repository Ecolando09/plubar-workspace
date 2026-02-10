#!/usr/bin/env python3
"""Weekly Wizdom Trading Bridge"""
import os
import sys
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv
import requests
import asyncio

load_dotenv()

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

WIZDOM_CHANNEL = os.environ.get("DISCORD_WEEKLY_WIZDOM_CHANNEL_ID")
WIZARD_CHANNEL = os.environ.get("DISCORD_WIZARD_OF_SOHO_CHANNEL_ID")
DANIELS_CHANNEL = os.environ.get("DISCORD_DANIELS_TRADES_CHANNEL_ID")

TRADE_KEYWORDS = [
    "entry", "entry price", "exit", "long", "short", "tp", "sl", "stop loss",
    "signal", "buy", "sell", "call", "put", "leverage", "margin", "futures",
    "options", "position size", "position", "squeeze", "breakout", "reversal",
    "accumulate", "take profit", "swing trade", "day trade", "leverage up"
]

IMPORTANT_USERS = ["wizardofsoho", "daniels", "wizard", "daniel"]

log_file = open("/tmp/wizdom-bridge.log", "a")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    log_file.write(line + "\n")
    log_file.flush()
    print(line, flush=True)

log("=" * 70)
log("Weekly Wizdom Trading Bridge Starting")
log("=" * 70)

client = TelegramClient("auth_session", API_ID, API_HASH)

def is_trade_message(text):
    if not text:
        return False
    text_lower = text.lower()
    return sum(1 for k in TRADE_KEYWORDS if k in text_lower) >= 2

async def forward_to_discord(message, sender, channel_id, emoji):
    if not channel_id:
        return
    text = message.text[:1800]
    payload = {"content": f"{emoji} **{sender}**\n{text}"}
    try:
        r = requests.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            json=payload,
            headers={"Authorization": f"Bot {DISCORD_TOKEN}"},
            timeout=5
        )
        if r.status_code == 200:
            log(f"Forwarded to Discord")
    except Exception as e:
        log(f"Discord error: {e}")

async def main():
    await client.connect()
    
    dialogs = await client.get_dialogs()
    channel = None
    for d in dialogs:
        if hasattr(d.entity, "title") and d.entity.title == "Weekly Wizdom":
            channel = d.entity
            break
    
    if not channel:
        log("Weekly Wizdom not found!")
        return
    
    log(f"Monitoring: {channel.title}")
    log("-" * 70)
    
    last_id = None
    
    while True:
        try:
            msgs = await client.get_messages(channel, limit=15)
            
            for m in reversed(msgs):
                if not m.text or (last_id and m.id <= last_id):
                    continue
                last_id = max(last_id or 0, m.id)
                
                sender = "Unknown"
                sender_is_important = False
                if m.sender:
                    sender = m.sender.username or m.sender.first_name
                    sender_lower = (m.sender.username or "").lower()
                    sender_is_important = sender_lower in IMPORTANT_USERS
                
                is_trade = is_trade_message(m.text)
                
                if not (is_trade or sender_is_important):
                    continue
                
                discord_channel = None
                emoji = "📈"
                
                if sender_is_important:
                    if "wizard" in sender_lower:
                        discord_channel = WIZARD_CHANNEL
                        emoji = "🧙‍♂️"
                        log(f"🧙‍♂️ {sender}: {m.text[:60]}...")
                    elif "daniel" in sender_lower:
                        discord_channel = DANIELS_CHANNEL
                        emoji = "📊"
                        log(f"📊 {sender}: {m.text[:60]}...")
                elif is_trade:
                    discord_channel = WIZDOM_CHANNEL
                    emoji = "🚨"
                    log(f"🚨 {sender}: {m.text[:60]}...")
                
                if discord_channel:
                    await forward_to_discord(m, sender, discord_channel, emoji)
            
            await asyncio.sleep(5)
            
        except Exception as e:
            log(f"Error: {e}")
            await asyncio.sleep(60)

asyncio.run(main())
