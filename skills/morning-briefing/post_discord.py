#!/usr/bin/env python3
"""Post morning briefing to Discord via webhook"""

import json
import sys
import os
from datetime import datetime

# Load webhook from config file if available
CONFIG_FILE = "/root/.openclaw/workspace/.morning_briefing.env"

def load_webhook():
    """Load webhook URL from config file or environment"""
    # Check environment first
    webhook = os.environ.get('DISCORD_WEBHOOK_URL', '')
    if webhook:
        return webhook
    
    # Load from config file
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                if line.startswith('DISCORD_WEBHOOK_URL='):
                    return line.strip().split('=', 1)[1].strip()
    return ''

WEBHOOK_URL = load_webhook()
CHANNEL_ID = os.environ.get('DISCORD_CHANNEL_ID', WEBHOOK_URL)

def post_to_discord():
    """Post briefing embed to Discord"""
    today = datetime.now().strftime('%Y-%m-%d')
    json_path = f"/root/.openclaw/workspace/outputs/daily/briefing_{today}.json"
    
    if not os.path.exists(json_path):
        print(f"❌ Briefing not found: {json_path}")
        return False
    
    # Load the embed JSON
    with open(json_path) as f:
        embed = json.load(f)
    
    # If webhook URL provided, post directly
    if WEBHOOK_URL:
        import urllib.request
        
        payload = {"embeds": [embed]}
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'OpenClaw-MorningBriefing'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status in [200, 204]:
                    print("✅ Posted to Discord via webhook!")
                    return True
                else:
                    print(f"❌ Discord error: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Failed to post: {e}")
            return False
    
    # Otherwise output curl command
    else:
        print("📋 Discord webhook not configured.")
        print(f"\nTo enable, set DISCORD_WEBHOOK_URL:")
        print(f"  export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/...'\n")
        print("Or add to cron with channel ID:")
        print(f"  DISCORD_CHANNEL_ID={CHANNEL_ID} python3 {sys.argv[0]}")
        print(f"\nCurl command:")
        print(f"  curl -X POST '{CHANNEL_ID}' -H 'Content-Type: application/json' -d @{json_path}")
        return False

if __name__ == "__main__":
    post_to_discord()
