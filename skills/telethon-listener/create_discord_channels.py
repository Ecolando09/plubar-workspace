#!/usr/bin/env python3
"""Create Discord channels for trading signals"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
GUILD_ID = '1468813158532776177'  # Your server

if not TOKEN:
    print("Error: DISCORD_BOT_TOKEN not set in .env")
    exit(1)

headers = {'Authorization': f'Bot {TOKEN}'}

# Channels to create
channels = [
    ('🧙‍♂️-wizard-of-soho', 'Official trades and announcements from Wizard of Soho', 10800),
    ('📊-daniels-trades', 'Trade calls and signals from Daniels', 10800),
    ('💬-weekly-wizdom', 'Weekly Wizdom / Money Glitch general chat', 10800),
    ('🎯-abullish-options', 'Options calls from Abullish', 10800),
]

print(f"Creating channels in guild {GUILD_ID}...")
print(f"Token: {TOKEN[:20]}...")

for name, topic, _ in channels:
    payload = {
        'name': name,
        'topic': topic,
        'type': 0  # Text channel
    }
    
    r = requests.post(
        f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels',
        json=payload,
        headers=headers
    )
    
    if r.status_code in [200, 201]:
        ch = r.json()
        print(f"✓ Created: #{name} (ID: {ch['id']})")
        # Update .env with this channel ID
        env_name = name.replace('🎯', '').replace('🧙‍♂️', '').replace('📊', '').replace('💬', '').replace('-', '_').upper().strip()
        print(f"  Env var: DISCORD_{env_name}_CHANNEL_ID = {ch['id']}")
    else:
        print(f"✗ Error creating #{name}: {r.status_code} {r.text[:100]}")

