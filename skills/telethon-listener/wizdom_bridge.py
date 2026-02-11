#!/usr/bin/env python3
"""Weekly Wizdom Chat Bridge - All trading & discussion
Optimized for maximum information capture from Weekly Wizdom Telegram channel
"""
import os
import sys
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv
import requests
import asyncio
import atexit

load_dotenv()

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

WIZDOM_CHANNEL = os.environ.get("DISCORD_WEEKLY_WIZDOM_CHANNEL_ID")
WIZARD_CHANNEL = os.environ.get("DISCORD_WIZARD_OF_SOHO_CHANNEL_ID")
DANIELS_CHANNEL = os.environ.get("DISCORD_DANIELS_TRADES_CHANNEL_ID")
ABULLISH_CHANNEL = os.environ.get("DISCORD_ABULLISH_OPTIONS_CHANNEL_ID")

# Trade signals (high priority) - Expanded keyword list
TRADE_KW = [
    "entry", "exit", "long", "short", "tp", "sl", "stop loss", "stop loss", "buy price",
    "signal", "buy", "sell", "call", "put", "leverage", "margin", "futures",
    "options", "position size", "squeeze", "breakout", "reversal",
    "take profit", "swing trade", "leverage up", "liquidation", "funding",
    "open position", "close position", "add to position", "scale in", "scale out",
    "stop out", "limit order", "market order", "pending order", "avg price",
    "pnl", "profit", "loss", "roi", "r:r", "risk reward", " Kelly criterion",
    "delta", "gamma", "theta", "vega", "open interest", "oi", "volume profile",
    "order book", "bid", "ask", "spread", "fill", "execution", "slippage",
    "notional", "collateral", "isolated", "cross margin", "adjust", "hedge"
]

# Market discussion (medium priority) - Expanded keyword list
MARKET_KW = [
    "market", "trend", "bullish", "bearish", "pump", "crash", "dump", "rally",
    "volume", "resistance", "support", "chart", "analysis", "opinion", "outlook",
    "bitcoin", "btc", "eth", "crypto", "alts", "sentiment", "session", "open",
    "close", "high", "low", "range", "consolidation", "consolidating", "volatile",
    "volatility", "impulse", "pullback", "retest", "rejection", "wick", "candle",
    "pattern", "wedge", "flag", "triangle", "pennant", "head and shoulders",
    "double top", "double bottom", "ascending", "descending", "symmetrical",
    "macd", "rsi", "stoch", "bollinger", "ema", "sma", "ma", "obv", "atr",
    "fibonacci", "pivot", "trendline", "channels", "timeframe", "tf", "mfi", "vwap"
]

# General chat (lower priority) - Keywords for community discussion
CHAT_KW = [
    "what do you think", "anyone else", "feeling", "opinion", "agree", "disagree",
    "moon", "rekt", "missed", "lambo", "to the moon", "green", "red", "profit",
    "loss", "paper hands", "diamond hands", "bags", "holding", "hodl", "sold",
    "bought", "watching", "waiting", "looks like", "seems like", "might", "could",
    "probably", "perhaps", "maybe", "anyone", "everyone", "someone", "people",
    "traders", "trading", "investors", "investing", "portfolio", "allocation"
]

# Important users map with their dedicated channels
IMPORTANT_USERS = {
    "wizardofsoho": {"channel": WIZARD_CHANNEL, "emoji": "🧙‍♂️", "name": "Wizard"},
    "wizard": {"channel": WIZARD_CHANNEL, "emoji": "🧙‍♂️", "name": "Wizard"},
    "daniels": {"channel": DANIELS_CHANNEL, "emoji": "📊", "name": "Daniels"},
    "daniel": {"channel": DANIELS_CHANNEL, "emoji": "📊", "name": "Daniels"},
    "abullish": {"channel": ABULLISH_CHANNEL, "emoji": "🎯", "name": "ABullish"},
}

# Rate limiting for Discord API
discord_rate_limit = {"tokens": 5, "last_refill": datetime.now().timestamp()}
MAX_DISCORD_RETRIES = 3

log_file = open("/tmp/wizdom-bridge.log", "a")
atexit.register(lambda: log_file.close())

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
    """Categorize message by content type with priority scoring."""
    if not text:
        return None, 0
    
    text_lower = text.lower()
    
    # High priority: trade signals (only 1 keyword needed for trading context)
    trade_count = sum(1 for k in TRADE_KW if k in text_lower)
    if trade_count >= 1:
        return "🚨 SIGNAL", 3
    
    # Medium priority: market discussion (2+ keywords)
    market_count = sum(1 for k in MARKET_KW if k in text_lower)
    if market_count >= 2:
        return "📈 MARKET", 2
    
    # Lower priority: general chat with keywords (2+ keywords)
    chat_count = sum(1 for k in CHAT_KW if k in text_lower)
    if chat_count >= 2:
        return "💬 CHAT", 1
    
    return None, 0

async def check_discord_rate_limit():
    """Simple rate limiting for Discord API."""
    now = datetime.now().timestamp()
    if now - discord_rate_limit["last_refill"] >= 1:
        discord_rate_limit["tokens"] = 5
        discord_rate_limit["last_refill"] = now
    return discord_rate_limit["tokens"] > 0

async def consume_discord_token():
    discord_rate_limit["tokens"] -= 1

async def forward_to_discord(message, sender, channel_id, emoji, category):
    """Forward message to Discord with retry logic."""
    if not channel_id:
        log(f"⚠️ No Discord channel configured for this message")
        return False
    
    # Get message text safely (handle different message types)
    text = ""
    if hasattr(message, 'text') and message.text:
        text = message.text
    elif hasattr(message, 'message') and message.message:
        text = message.message
    else:
        log(f"⚠️ No text content in message")
        return False
    
    # Truncate for Discord
    text = str(text)[:1900]
    clean_text = text.replace("**", "*").replace("__", "_").replace("`", "").replace("```", "")
    
    # Add media indicator if present
    media_indicator = ""
    if message.media:
        if hasattr(message.media, 'photo') and message.media.photo:
            media_indicator = " [📷 PHOTO]"
        elif hasattr(message.media, 'document') and message.media.document:
            media_indicator = " [📎 FILE]"
        else:
            media_indicator = " [📎 MEDIA]"
    
    content = f"{emoji} **{sender}** {category}\n{clean_text}{media_indicator}"
    payload = {"content": content}
    
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    
    for attempt in range(MAX_DISCORD_RETRIES):
        try:
            # Check rate limit
            if not await check_discord_rate_limit():
                await asyncio.sleep(0.5)
            
            r = requests.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            await consume_discord_token()
            
            if r.status_code == 200:
                log(f"✓ Forwarded [{category.strip()}]: {sender[:20]}")
                return True
            elif r.status_code == 429:
                # Rate limited, wait and retry
                wait_time = int(r.headers.get('Retry-After', 1))
                log(f"⚠️ Discord rate limited, waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            else:
                log(f"✗ Discord API error {r.status_code}: {r.text[:100]}")
                await asyncio.sleep(2)
                
        except Exception as e:
            log(f"✗ Discord error (attempt {attempt+1}): {e}")
            await asyncio.sleep(2)
    
    return False

async def main():
    """Main monitoring loop with improved error handling."""
    log("=" * 70)
    log("Weekly Wizdom Bridge - OPTIMIZED VERSION")
    log("=" * 70)
    
    # Validate configuration
    missing_configs = []
    if not API_ID or not API_HASH:
        missing_configs.append("API_ID / API_HASH")
    if not DISCORD_TOKEN:
        missing_configs.append("DISCORD_BOT_TOKEN")
    if not WIZDOM_CHANNEL:
        missing_configs.append("DISCORD_WEEKLY_WIZDOM_CHANNEL_ID")
    
    if missing_configs:
        log(f"⚠️ Missing configuration: {', '.join(missing_configs)}")
        log("⚠️ Running in console-only mode (no Discord forwarding)")
    
    try:
        await client.connect()
        log("✓ Connected to Telegram")
    except Exception as e:
        log(f"✗ Failed to connect to Telegram: {e}")
        return
    
    # Find the channel
    channel = None
    try:
        dialogs = await client.get_dialogs()
        for d in dialogs:
            if hasattr(d.entity, "title") and d.entity.title == "Weekly Wizdom":
                channel = d.entity
                break
    except Exception as e:
        log(f"✗ Failed to get dialogs: {e}")
        return
    
    if not channel:
        log("✗ Weekly Wizdom channel not found!")
        return
    
    log(f"✓ Monitoring: {channel.title} (ID: {channel.id})")
    log(f"✓ Trade keywords: {len(TRADE_KW)} | Market keywords: {len(MARKET_KW)} | Chat keywords: {len(CHAT_KW)}")
    log(f"✓ Important users: {', '.join(IMPORTANT_USERS.keys())}")
    log("-" * 70)
    
    last_id = None
    reconnect_attempts = 0
    max_reconnect_attempts = 5
    
    while True:
        try:
            # Fetch messages
            msgs = await client.get_messages(channel, limit=30)
            
            for m in reversed(msgs):
                # Skip if no content or already processed
                if not m.text and not m.message:
                    continue
                if last_id and m.id <= last_id:
                    continue
                last_id = max(last_id or 0, m.id)
                
                # Get sender info
                sender = "Unknown"
                sender_is_important = False
                sender_info = None
                
                if m.sender:
                    sender_username = getattr(m.sender, 'username', None) or ""
                    sender_firstname = getattr(m.sender, 'first_name', "") or ""
                    sender = sender_username or sender_firstname or "Unknown"
                    sender_lower = sender_username.lower() if sender_username else ""
                    
                    # Check if important user
                    if sender_lower in IMPORTANT_USERS:
                        sender_is_important = True
                        sender_info = IMPORTANT_USERS[sender_lower]
                
                # Categorize message
                message_text = m.text or m.message or ""
                category, priority = categorize_message(message_text)
                
                # Important users always get forwarded
                if sender_is_important and sender_info:
                    emoji = sender_info["emoji"]
                    channel_id = sender_info["channel"]
                    category_display = f"[👑 {sender_info['name']}]"
                elif category:
                    emoji = "📊"
                    channel_id = WIZDOM_CHANNEL
                    category_display = category
                else:
                    # Low priority messages - still capture if they have some keywords
                    keyword_count = sum(1 for k in TRADE_KW + MARKET_KW if k in message_text.lower())
                    if keyword_count >= 1:
                        emoji = "💬"
                        channel_id = WIZDOM_CHANNEL
                        category_display = "[📝 CAPTURED]"
                    else:
                        continue
                
                # Log what we're capturing
                display_sender = sender[:25] if len(sender) > 25 else sender
                display_text = (message_text[:50].replace("\n", " ") + "...") if len(message_text) > 50 else message_text.replace("\n", " ")
                log(f"{emoji} {category_display} {display_sender}: {display_text}")
                
                # Forward to Discord
                if channel_id:
                    success = await forward_to_discord(m, sender, channel_id, emoji, category_display)
                    if not success:
                        log(f"✗ Failed to forward message {m.id}")
            
            # Reset reconnect counter on success
            reconnect_attempts = 0
            
            # Polling interval - faster for real-time feel
            await asyncio.sleep(6)
            
        except asyncio.CancelledError:
            log("✓ Shutting down...")
            break
        except Exception as e:
            reconnect_attempts += 1
            log(f"✗ Error (attempt {reconnect_attempts}/{max_reconnect_attempts}): {e}")
            
            if reconnect_attempts >= max_reconnect_attempts:
                log("✗ Max reconnect attempts reached, restarting...")
                try:
                    await client.disconnect()
                except:
                    pass
                await asyncio.sleep(5)
                await client.connect()
                reconnect_attempts = 0
            else:
                await asyncio.sleep(30)
    
    await client.disconnect()
    log("✓ Disconnected from Telegram")

asyncio.run(main())
