# BIRB Tracker Skill

Track Moonbirds NFT and $BIRB token prices with price change alerts.

## Description

Fetches current prices for Moonbirds, Oddities, Mythics, and $BIRB token from CoinGecko. Calculates 24h changes and alerts on significant movements (>10%).

## Use When

- User asks about Moonbirds or BIRB prices
- Need to track NFT floor changes
- User wants price alerts configured
- Checking portfolio value changes

## Don't Use When

- User asks about general crypto prices (→ `brave-search` or use CoinGecko directly)
- User asks about NFT projects other than Moonbirds family
- User wants trading signals (→ not a trading bot)
- User asks about NFT rarity/attributes (→ use Moonbirds official tools)

## Inputs

- `symbol`: Token symbol (default: `birb`)
- `threshold`: Alert threshold percentage (default: `10`)
- `networks`: Networks to check (optional)

## Outputs

- Current prices in USD and ETH
- 24h price change percentage
- Floor prices for all Moonbirds collections
- Alert if threshold exceeded

## Examples

### Get current prices
```bash
python3 /root/.openclaw/workspace/skills/birb-tracker/tracker.py
```

### Check with custom threshold
```bash
THRESHOLD=15 python3 /root/.openclaw/workspace/skills/birb-tracker/tracker.py
```

## Dependencies

- requests
- python-dateutil

## Notes

- Uses CoinGecko free API (rate limited)
- Prices cached for 60 seconds
- Alert output sent to configured channels (Discord)
