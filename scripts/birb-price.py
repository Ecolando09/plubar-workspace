#!/usr/bin/env python3
"""$BIRB Token + NFT Floor Tracker - Discord-Ready Output"""
import requests
import json
import os
from datetime import datetime

# Configuration
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/moonbirds"
ALCHEMY_URL = "https://eth-mainnet.g.alchemy.com/nft/v3/demo/getFloorPrice"
NFT_CONTRACTS = {
    'Moonbirds': '0x23581767a106ae21c074b2276d25e5c3e136a68b',
    'Oddities': '0x1792a96e5668ad7c167ab804a100ce42395ce54d',
    'Mythics': '0xc0ffee8ff7e5497c2d6f7684859709225fcc5be8',
}
HISTORY_FILE = "/root/.openclaw/workspace/.birb-price-history.json"

# Color indicators
GREEN = "🟢"
RED = "🔴"
YELLOW = "🟡"

def format_number(num):
    """Format large numbers with K/M/B suffixes"""
    if num is None:
        return "N/A"
    if num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    if num >= 1_000:
        return f"${num/1_000:.2f}K"
    return f"${num:.2f}"

def format_percent(val):
    """Format percentage with emoji"""
    if val is None:
        return f"{YELLOW} N/A"
    emoji = GREEN if val > 0 else RED if val < 0 else YELLOW
    sign = "+" if val > 0 else ""
    return f"{emoji} {sign}{val:.2f}%"

def load_history():
    """Load historical price data"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_history(data):
    """Save current prices to history"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_birb_data():
    """Fetch $BIRB data from CoinGecko API"""
    try:
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }
        response = requests.get(COINGECKO_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ CoinGecko API Error: {e}")
        return None

def get_nft_floors():
    """Fetch NFT floor prices from Alchemy API"""
    floors = {}
    for name, contract in NFT_CONTRACTS.items():
        try:
            r = requests.get(f"{ALCHEMY_URL}?contractAddress={contract}", timeout=5)
            floors[name] = r.json().get('openSea', {}).get('floorPrice')
        except:
            floors[name] = None
    return floors

def parse_coin_data(data):
    """Parse CoinGecko response for key metrics"""
    if not data:
        return None
    
    market_data = data.get("market_data", {})
    
    return {
        "name": data.get("name", "Birb"),
        "symbol": data.get("symbol", "BIRB").upper(),
        "current_price": market_data.get("current_price", {}).get("usd", 0),
        "price_change_24h": market_data.get("price_change_percentage_24h", 0),
        "price_change_7d": market_data.get("price_change_percentage_7d", 0),
        "price_change_30d": market_data.get("price_change_percentage_30d", 0),
        "market_cap": market_data.get("market_cap", {}).get("usd", 0),
        "market_cap_rank": data.get("market_cap_rank", None),
        "volume_24h": market_data.get("total_volume", {}).get("usd", 0),
        "circulating_supply": market_data.get("circulating_supply", 0),
        "total_supply": market_data.get("total_supply", 0),
        "high_24h": market_data.get("high_24h", {}).get("usd", 0),
        "low_24h": market_data.get("low_24h", {}).get("usd", 0),
        "ath": market_data.get("ath", {}).get("usd", 0),
        "ath_change": market_data.get("ath_change_percentage", {}).get("usd", 0),
        "atl": market_data.get("atl", {}).get("usd", 0),
        "last_updated": data.get("last_updated", datetime.now().isoformat())
    }

def get_ath_emoji(current, ath):
    """Get emoji based on distance from ATH"""
    if not ath or not current:
        return YELLOW
    pct = ((ath - current) / ath) * 100
    if pct < 5:
        return "🔥"
    if pct < 20:
        return "📈"
    if pct < 50:
        return "📊"
    return "💤"

def get_nft_change_emoji(current, old):
    """Get emoji for NFT price change"""
    if old is None or current is None or old == 0:
        return ""
    pct = ((current - old) / old) * 100
    if pct > 0:
        return f" {GREEN}{pct:+.1f}%"
    elif pct < 0:
        return f" {RED}{pct:.1f}%"
    return " ⚪0.0%"

def generate_discord_output(metrics, old_price, nft_floors, old_nft_floors):
    """Generate Discord-ready formatted output"""
    name = metrics["name"]
    symbol = metrics["symbol"]
    price = metrics["current_price"]
    change_24h = metrics["price_change_24h"]
    change_30d = metrics["price_change_30d"]
    mcap = metrics["market_cap"]
    volume = metrics["volume_24h"]
    rank = metrics["market_cap_rank"]
    circulating = metrics["circulating_supply"]
    high_24h = metrics["high_24h"]
    low_24h = metrics["low_24h"]
    ath = metrics["ath"]
    ath_change = metrics["ath_change"]
    atl = metrics["atl"]
    updated = metrics["last_updated"]
    
    # Price direction emoji
    if change_24h > 0:
        direction = "🚀"
    elif change_24h < 0:
        direction = "📉"
    else:
        direction = "➡️"
    
    # Calculate local change from history
    local_change = None
    if old_price and old_price > 0:
        local_change = ((price - old_price) / old_price) * 100
    
    ath_emoji = get_ath_emoji(price, ath)
    
    output = []
    output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    output.append(f"   {direction} **{name} ({symbol}) PRICE REPORT** {direction}")
    output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    output.append("")
    output.append(f"💰 **${price:.6f} USD**")
    output.append("")
    output.append("📊 **PERFORMANCE**")
    output.append(f"   24h:  {format_percent(change_24h)}")
    output.append(f"   30d:  {format_percent(change_30d)}")
    if local_change is not None:
        output.append(f"   Local: {format_percent(local_change)}")
    output.append("")
    output.append("📈 **MARKET DATA**")
    output.append(f"   Cap:   **{format_number(mcap)}**")
    output.append(f"   Vol:   {format_number(volume)}")
    if rank:
        output.append(f"   Rank:  #{rank}")
    output.append(f"   Circ:  {format_number(circulating)}")
    output.append("")
    output.append(f"🔮 **24H RANGE**  ${low_24h:.4f} — ${high_24h:.4f}")
    output.append("")
    output.append(f"{ath_emoji} **ALL-TIME**")
    output.append(f"   ATH:  ${ath:.4f} ({ath_change:.1f}%)")
    output.append(f"   ATL:  ${atl:.4f}")
    output.append("")
    output.append(f"🕐 Updated: `{updated[:19]}` UTC")
    output.append("")
    output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    output.append("🖼️ **NFT FLOORS (OpenSea)**")
    output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    for collection, floor in nft_floors.items():
        old_floor = old_nft_floors.get(collection, floor) if old_nft_floors else floor
        change = get_nft_change_emoji(floor, old_floor)
        if floor:
            output.append(f"   {collection:12} **{floor:.4f} ETH**{change}")
        else:
            output.append(f"   {collection:12} N/A")
    
    output.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(output)

def main():
    """Main execution"""
    print("🐦 Fetching price data...")
    
    # Load history
    history = load_history()
    old_price = history.get("birb", {}).get("price", None)
    old_nft_floors = history.get("nfts", {})
    
    # Get $BIRB data from CoinGecko
    raw_data = get_birb_data()
    
    if not raw_data:
        print("❌ Failed to fetch $BIRB data")
        if old_price:
            print(f"📊 Cached: ${old_price:.6f}")
        return 1
    
    # Parse $BIRB data
    metrics = parse_coin_data(raw_data)
    
    # Get NFT floors
    nft_floors = get_nft_floors()
    
    # Update history
    history["birb"] = {
        "price": metrics["current_price"],
        "time": metrics["last_updated"]
    }
    history["nfts"] = nft_floors
    save_history(history)
    
    # Generate output
    output = generate_discord_output(metrics, old_price, nft_floors, old_nft_floors)
    print()
    print(output)
    
    return 0

if __name__ == "__main__":
    exit(main())
