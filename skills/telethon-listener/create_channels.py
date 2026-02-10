#!/usr/bin/env python3
"""Create Discord channels for trading signals"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
GUILD_ID = os.environ.get('DISCORD_GUILD_ID')

headers = {'Authorization': f'Bot {TOKEN}'}

# Channels to create
channels = [
    ('🧙‍♂️-wizard-of-soho', 'Official trades and announcements from Wizard of Soho'),
    ('📊-daniels-trades', 'Trade calls and signals from Daniels'),
    ('💬-weekly-wizdom', 'Weekly Wizdom / Money Glitch general chat'),
    ('🎯-abullish-options', 'Options calls from Abullish'),
]

print(f"Creating channels in guild {GUILD_ID}...")
created = {}

for name, topic in channels:
    payload = {'name': name, 'topic': topic, 'type': 0}
    
    r = requests.post(
        f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels',
        json=payload,
        headers=headers
    )
    
    if r.status_code in [200, 201]:
        ch = r.json()
        print(f"✓ Created: #{name} (ID: {ch['id']})")
        created[name] = ch['id']
    else:
        print(f"✗ Error: {r.status_code} {r.text[:100]}")

print("\nAdd these to .env:")
for name, cid in created.items():
    env_name = name.replace('🎯', '').replace('🧙‍♂️', '').replace('📊', '').replace('💬', '').replace('-', '_').upper().strip()
    print(f"DISCORD_{env_name}_CHANNEL_ID={cid}")
