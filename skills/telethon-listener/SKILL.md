# Telethon Listener

Listen to Telegram channels and forward messages to Discord or other platforms.

## Setup

1. Get API credentials from https://my.telegram.org:
   - Create an application
   - Get `API_ID` and `API_HASH`

2. Install dependencies:
```bash
pip install telethon python-dotenv
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Usage

### Listen to a Channel

```python
from telethon_listener import TelegramListener

async def handler(message):
    print(f"[{message.date}] {message.sender_id}: {message.text}")

listener = TelegramListener()
await listener.listen_to_channel('CHANNEL_ID', handler)
```

### Forward to Discord

```python
from telethon_listener import TelegramListener, DiscordForwarder

forwarder = DiscordForwarder(bot_token='YOUR_DISCORD_BOT', channel_id='DISCORD_CHANNEL_ID')
listener = TelegramListener()

await listener.listen_to_channel('CHANNEL_ID', forwarder.forward)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| API_ID | Telegram API ID |
| API_HASH | Telegram API hash |
| PHONE | Your phone number (for auth) |
| SESSION_NAME | Session name for persistence |

## When to Use

- Monitoring Telegram channels for updates
- Forwarding crypto/news alerts to Discord
- Archiving channel messages
