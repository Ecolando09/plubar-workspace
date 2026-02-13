# Wizdom Summary Skill

Summarize AI and crypto news from multiple sources using Wizdom API.

## Description

Fetches trending topics, AI news, and crypto insights from Wizdom API. Generates concise summaries highlighting key developments and market movements.

## Use When

- User wants AI news summary
- User asks about crypto market developments
- Morning briefing preparation
- Weekly market recap needed

## Don't Use When

- User asks for real-time prices (→ `birb-tracker`)
- User wants specific news articles (→ `brave-search`)
- User asks about trading advice (→ not supported)
- User wants entertainment/news content (→ use general web search)

## Inputs

- `category`: News category (`ai`, `crypto`, `all`)
- `hours`: How far back to look (default: 24)
- `limit`: Number of topics (default: 10)

## Outputs

- JSON summary with topics and insights
- Formatted message for Discord/other channels
- Saved to `/root/.openclaw/workspace/outputs/reports/`

## Examples

```bash
# Get AI news summary
python3 /root/.openclaw/workspace/skills/wizdom-summary/summary.py --category ai

# Get crypto news from last 48 hours
python3 /root/.openclaw/workspace/skills/wizdom-summary/summary.py --category crypto --hours 48

# Full weekly summary
python3 /root/.openclaw/workspace/skills/wizdom-summary/summary.py --category all --hours 168
```

## Dependencies

- requests
- wizdom-api (if available)

## Notes

- Uses Wizdom API for insights
- Can fallback to Brave Search if API unavailable
- Output format matches morning briefing requirements
