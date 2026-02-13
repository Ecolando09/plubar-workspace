#!/usr/bin/env python3
"""Track Moonbirds floor prices over time"""
import json
import os
from datetime import datetime

DATA_FILE = "/root/.openclaw/workspace/data/moonbirds_prices.json"

def load_prices():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_price(price):
    prices = load_prices()
    prices.append({
        "timestamp": datetime.utcnow().isoformat(),
        "floor_eth": price
    })
    # Keep last 168 entries (7 days at 1 hour intervals)
    prices = prices[-168:]
    with open(DATA_FILE, 'w') as f:
        json.dump(prices, f, indent=2)
    return prices

def generate_graph():
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from datetime import datetime
    
    prices = load_prices()
    if not prices:
        print("No data yet!")
        return
    
    dates = [datetime.fromisoformat(p['timestamp']) for p in prices]
    floors = [p['floor_eth'] for p in prices]
    
    plt.figure(figsize=(12, 6))
    plt.plot(dates, floors, 'b-', linewidth=2, marker='o', markersize=3)
    plt.fill_between(dates, floors, alpha=0.3)
    
    plt.title('Moonbirds NFT Floor Price (ETH)', fontsize=16)
    plt.xlabel('Date/Time', fontsize=12)
    plt.ylabel('Floor Price (ETH)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=12))
    plt.xticks(rotation=45)
    
    # Add current price annotation
    if floors:
        plt.annotate(f'Current: {floors[-1]:.4f} ETH',
                    xy=(dates[-1], floors[-1]),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=10, color='red')
    
    plt.tight_layout()
    plt.savefig('/root/.openclaw/workspace/data/moonbirds_chart.png', dpi=150)
    print(f"Saved to /root/.openclaw/workspace/data/moonbirds_chart.png")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'track':
            import requests
            r = requests.get("https://eth-mainnet.g.alchemy.com/nft/v3/demo/getFloorPrice?contractAddress=0x23581767a106ae21c074b2276d25e5c3e136a68b", timeout=5)
            floor = r.json().get('openSea', {}).get('floorPrice')
            if floor:
                save_price(floor)
                print(f"Saved: {floor} ETH")
        elif sys.argv[1] == 'graph':
            generate_graph()
    else:
        print("Usage: python moonbirds_tracker.py track|graph")
