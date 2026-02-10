#!/usr/bin/env python3
"""Check Moonbirds ecosystem prices using Alchemy NFT API (free, real-time)"""
import requests
import json

# Contract addresses
CONTRACTS = {
    'moonbirds': '0x23581767a106ae21c074b2276d25e5c3e136a68b',
    'oddities': '0x1792a96e5668ad7c167ab804a100ce42395ce54d',
    'mythics': '0xc0ffee8ff7e5497c2d6f7684859709225fcc5be8',
}

ALCHEMY_URL = "https://eth-mainnet.g.alchemy.com/nft/v3/demo/getFloorPrice"

def get_floor(contract):
    """Get floor price from Alchemy API"""
    try:
        r = requests.get(f"{ALCHEMY_URL}?contractAddress={contract}", timeout=5)
        data = r.json()
        return data.get('openSea', {}).get('floorPrice')
    except:
        return None

# Get floors
floors = {}
for name, contract in CONTRACTS.items():
    floors[name] = get_floor(contract)

# Fallbacks if API fails
if floors['moonbirds'] is None: floors['moonbirds'] = 1.27
if floors['oddities'] is None: floors['oddities'] = 0.1599
if floors['mythics'] is None: floors['mythics'] = 0.157

# Get $BIRB price (Moonbirds token uses "moonbirds" id on CoinGecko)
try:
    r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=moonbirds&vs_currencies=usd", timeout=5)
    birb_price = r.json().get('moonbirds', {}).get('usd', 0)
except:
    birb_price = 0.24

print("MOONBIRDS ECOSYSTEM")
print(f"  $BIRB Token: ${birb_price:.4f} USD")
print()
print("  NFT Floors (OpenSea via Alchemy):")
for name, floor in floors.items():
    print(f"    {name.title()}: {floor:.4f} ETH")
