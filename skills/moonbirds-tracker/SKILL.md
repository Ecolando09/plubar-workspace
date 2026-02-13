# Moonbirds Tracker Skill

Track Moonbirds NFT collection statistics and floor prices.

## Description

Monitors Moonbirds, Oddities, and Mythics floor prices. Tracks historical data and alerts on significant changes. Part of the BIRB ecosystem monitoring.

## Use When

- User asks about Moonbirds NFT floor
- Tracking NFT portfolio value
- BIRB ecosystem monitoring
- Setting floor price alerts

## Don't Use When

- User asks about $BIRB token price (→ `birb-tracker`)
- User asks about general NFT projects (→ `brave-search`)
- User wants rarity rankings (→ use Moonbirds official tools)
- User wants to buy/sell NFTs (→ not a marketplace)

## Inputs

- `collections`: Comma-separated list (`moonbirds,oddities,mythics`)
- `alert_threshold`: Price change % for alerts (default: 10)
- `hours`: Historical range (default: 24)

## Outputs

- Current floor prices in ETH
- 24h change percentage
- Collection comparison
- Alert if threshold exceeded

## Examples

```bash
# Standard check
python3 /root/.openclaw/workspace/skills/moonbirds-tracker/tracker.py

# All collections with 5% alert
python3 /root/.openclaw/workspace/skills/moonbirds-tracker/tracker.py --collections all --threshold 5

# Historical view
python3 /root/.openclaw/workspace/skills/moonbirds-tracker/tracker.py --hours 168
```

## Dependencies

- requests
- python-dateutil
- OpenSea API access (or similar)

## Notes

- Part of BIRB ecosystem skills
- Coordinates with `birb-tracker` for token prices
- Output can trigger Discord notifications
- Historical data stored in `/root/.openclaw/workspace/outputs/backups/`
