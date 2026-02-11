#!/usr/bin/env python3
"""Weekly Wizdom Chat Bridge - All trading & discussion"""
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
ABULLISH_CHANNEL = os.environ.get("DISCORD_ABULLISH_OPTIONS_CHANNEL_ID")

# Trade signals (high priority)
TRADE_KW = [
    "entry", "exit", "long", "short", "tp", "sl", "stop loss", "buy price",
    "signal", "buy", "sell", "call", "put", "leverage", "margin", "futures",
    "options", "position size", "squeeze", "breakout", "reversal",
    "take profit", "swing trade", "leverage up", " liquidation", "funding"
]

# Market discussion (medium priority)
MARKET_KW = [
    "market", "trend", "bullish", "bearish", "pump", "crash", "dump",
    "volume", "resistance", "support", "chart", "analysis", "opinion",
    "bitcoin", "btc", "eth", "crypto", "alts", "sentiment"
]

# General chat (lower priority)
CHAT_KW = [
    "what do you think", "anyone else", "feeling", "opinion", "agree",
    "moon", "rekt", "missed", "lambo", "to the moon", "green", "red"
]

IMPORTANT_USERS = ["wizardofsoho", "wizard", "daniels", "daniel", "abullish"]

log_file = open("/tmp/wizdom-bridge.log", "a")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    log_file.write(line + "\n")
    log_file.flush()
    print(line, flush=True)

log("=" * 70)
log("Weekly Wizdom Chat Bridge - ALL DISCUSSIONS")
log("=" * 70)

client = TelegramClient("auth_session", API_ID, API_HASH)

def categorize_message(text):
    if not text:
        return None, 0
    
    text_lower = text.lower()
    
    # High priority: trade signals
    trade_count = sum(1 for k in TRADE_KW if k in text_lower)
    if trade_count >= 1:
        return "SIGNAL", 3
    
    # Medium priority: market discussion
    market_count = sum(1 for k in MARKET_KW if k in text_lower)
    if market_count >= 2:
        return "MARKET", 2
    
    # Lower priority: general chat with keywords
    chat_count = sum(1 for k in CHAT_KW if k in text_lower)
    if chat_count >= 2:
        return "CHAT", 1
    
    return None, 0

async def forward_to_discord(message, sender, channel_id, emoji, category):
    if not channel_id:
        return
    text = message.text[:1900]
    clean_text = text.replace("**", "*").replace("__", "_")
    payload = {"content": f"{emoji} **{sender}** [{category}]\n{clean_text}"}
    try:
        r = requests.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            json=payload,
            headers={"Authorization": f"Bot {DISCORD_TOKEN}"},
            timeout=5
        )
        if r.status_code == 200:
            log(f"Forwarded [{category}]: {sender[:20]}")
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
    log("Keywords: Signals, Market discussion, General chat")
    log("-" * 70)
    
    last_id = None
    seen_today = set()
    
    while True:
        try:
            msgs = await client.get_messages(channel, limit=20)
            
            for m in reversed(msgs):
                if not m.text or (last_id and m.id <= last_id):
                    continue
                last_id = max(last_id or 0, m.id)
                
                sender = "Unknown"
                sender_is_important = False
                sender_lower = ""
                
                if m.sender:
                    sender = m.sender.username or m.sender.first_name or "Unknown"
                    sender_lower = (m.sender.username or "").lower()
                    sender_is_important = sender_lower in IMPORTANT_USERS
                
                category, priority = categorize_message(m.text)
                
                # Important users always get forwarded
                if sender_is_important:
                    category = "👑"
                    priority = 4
                
                if not category and not sender_is_important:
                    continue
                
                # Choose channel and emoji
                discord_channel = WIZDOM_CHANNEL
                emoji = "📊"
                
                if sender_is_important:
                    if "wizard" in sender_lower:
                        discord_channel = WIZARD_CHANNEL
                        emoji = "🧙‍♂️"
                    elif "daniel" in sender_lower:
                        discord_channel = DANIELS_CHANNEL
                        emoji = "📊"
                    elif "abullish" in sender_lower:
                        discord_channel = ABULLISH_CHANNEL
                        emoji = "🎯"
                elif category == "SIGNAL":
                    discord_channel = WIZDOM_CHANNEL
                    emoji = "🚨"
                elif category == "MARKET":
                    emoji = "📈"
                else:
                    emoji = "💬"
                
                # Log what we're capturing
                display_sender = sender[:25] if len(sender) > 25 else sender
                display_text = m.text[:50].replace("\n", " ")
                log(f"{emoji} [{category or 'IMPORTANT'}] {display_sender}: {display_text}...")
                
                if discord_channel:
                    await forward_to_discord(m, sender, discord_channel, emoji, category or "👑")
            
            await asyncio.sleep(8)
            
        except Exception as e:
            log(f"Error: {e}")
            await asyncio.sleep(30)

asyncio.run(main())
