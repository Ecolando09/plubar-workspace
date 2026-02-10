#!/usr/bin/env python3
"""Track Moonbirds floor prices - weekly and yearly charts"""
import json
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone, timedelta

DATA_DIR = "/root/.openclaw/workspace/data"
WEEKLY_FILE = f"{DATA_DIR}/moonbirds_weekly.json"
YEARLY_FILE = f"{DATA_DIR}/moonbirds_yearly.json"

def get_week_start(dt=None):
    """Get start of current week (Monday UTC 00:00)"""
    if dt is None:
        dt = datetime.now(timezone.utc)
    # weekday(): Monday=0, Sunday=6
    days_since_monday = dt.weekday()
    week_start = dt - timedelta(days=days_since_monday)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    return week_start

def get_year_start(dt=None):
    """Get start of current year (January 1st UTC 00:00)"""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def track_price(price):
    """Track current price in both weekly and yearly datasets"""
    now = datetime.now(timezone.utc)
    
    # Weekly
    weekly = load_json(WEEKLY_FILE)
    weekly.append({"timestamp": now.isoformat(), "floor_eth": price})
    # Reset if new week
    week_start = get_week_start(now)
    weekly = [p for p in weekly if datetime.fromisoformat(p['timestamp']) >= week_start]
    save_json(WEEKLY_FILE, weekly)
    
    # Yearly
    yearly = load_json(YEARLY_FILE)
    yearly.append({"timestamp": now.isoformat(), "floor_eth": price})
    # Reset if new year
    year_start = get_year_start(now)
    yearly = [p for p in yearly if datetime.fromisoformat(p['timestamp']) >= year_start]
    save_json(YEARLY_FILE, yearly)
    
    print(f"Tracked: {price} ETH")
    return weekly, yearly

def generate_chart(data, title, filename, figsize=(12, 6)):
    """Generate a chart from price data"""
    if not data:
        print(f"No data for {title}")
        return
    
    dates = [datetime.fromisoformat(p['timestamp']) for p in data]
    floors = [p['floor_eth'] for p in data]
    
    plt.figure(figsize=figsize)
    plt.plot(dates, floors, 'b-', linewidth=2, marker='o', markersize=4)
    plt.fill_between(dates, floors, alpha=0.3)
    
    plt.title(title, fontsize=16)
    plt.xlabel('Date/Time (UTC)', fontsize=12)
    plt.ylabel('Floor Price (ETH)', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=24))
    plt.xticks(rotation=45)
    
    # Current price annotation
    if floors:
        plt.annotate(f'Current: {floors[-1]:.4f} ETH',
                    xy=(dates[-1], floors[-1]),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=12, color='red', fontweight='bold')
    
    plt.tight_layout()
    filepath = f"{DATA_DIR}/{filename}"
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def generate_all():
    """Generate both weekly and yearly charts"""
    weekly = load_json(WEEKLY_FILE)
    yearly = load_json(YEARLY_FILE)
    
    print(f"Weekly: {len(weekly)} points, Yearly: {len(yearly)} points")
    
    generate_chart(weekly, 'Moonbirds Floor - This Week (ETH)', 'moonbirds_weekly.png')
    generate_chart(yearly, 'Moonbirds Floor - This Year (ETH)', 'moonbirds_yearly.png', figsize=(14, 7))

if __name__ == '__main__':
    import sys
    import requests
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'track':
            # Fetch current price from Alchemy
            r = requests.get(
                "https://eth-mainnet.g.alchemy.com/nft/v3/demo/getFloorPrice?contractAddress=0x23581767a106ae21c074b2276d25e5c3e136a68b",
                timeout=5
            )
            floor = r.json().get('openSea', {}).get('floorPrice')
            if floor:
                track_price(floor)
        
        elif cmd == 'graph' or cmd == 'charts':
            generate_all()
        
        elif cmd == 'status':
            weekly = load_json(WEEKLY_FILE)
            yearly = load_json(YEARLY_FILE)
            print(f"Weekly: {len(weekly)} prices tracked")
            print(f"Yearly: {len(yearly)} prices tracked")
    
    else:
        print("Usage: python moonbirds_charts.py track|graph|status")
