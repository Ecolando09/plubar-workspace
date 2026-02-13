# Morning Briefing Skill

Generate daily morning briefing with weather forecast, crypto prices, AI news, viral posts, and newsletter summaries.

## Description

Produces a comprehensive morning briefing combining:
- **Weather forecast** (highs, lows, rain chance, sunrise/sunset)
- **Crypto prices** (Moonbirds/BIRB)
- **Viral posts** (OpenClaw/AI trending content)
- **Newsletter summaries** (via Gmail/Substack integration)
- **Apps status** (all family apps)

Designed for automated cron execution at 8AM EST.

## Use When

- User requests morning briefing
- Cron job triggers daily update
- User wants comprehensive daily summary
- Morning routine automation needed

## Don't Use When

- User wants quick price check (→ `birb-tracker`)
- User wants specific news article (→ `brave-search`)
- User wants real-time trading (→ not supported)
- User asks for evening/specific time briefing (→ run manually with parameters)

## Inputs

- `output_path`: Where to save briefing (default: `/root/.openclaw/workspace/outputs/daily/`)
- `format`: Output format (`text`, `markdown`, `json`)
- `location`: Latitude/longitude (default: Spartanburg, SC)

## Outputs

- Briefing saved to `/root/.openclaw/workspace/outputs/daily/briefing_YYYY-MM-DD.md`
- JSON summary for programmatic use
- Formatted message for Discord delivery

## Examples

```bash
# Standard morning briefing
python3 /root/.openclaw/workspace/skills/morning-briefing/briefing.py

# JSON format for APIs
python3 /root/.openclaw/workspace/skills/morning-briefing/briefing.py --format json

# Custom output path
python3 /root/.openclaw/workspace/skills/morning-briefing/briefing.py --output /tmp/briefing.md
```

## Dependencies

- `requests` or `urllib` (weather API)
- `python-dateutil`
- `gog` CLI configured for Gmail newsletter access (optional)
- Templates in `skills/morning-briefing/templates/`

## Newsletter Setup

To enable newsletter summaries:

```bash
# Install gog CLI
brew install steipete/tap/gogcli  # macOS
# Or: curl -s https://gogcli.sh/install | bash  # Linux

# Configure OAuth
gog auth credentials /path/to/client_secret.json
gog auth add you@gmail.com --services gmail

# Test newsletter access
gog gmail search 'from:theinnermostloop@substack.com' --max 1
```

## Notes

- Runs automatically via cron at 8AM EST
- Weather uses Open-Meteo (free, no API key)
- Viral posts use Brave Search API (requires `BRAVE_API_KEY`)
- Newsletter requires `gog` Gmail OAuth configuration
- Templates loaded from skill folder (not embedded)
- Outputs to `/root/.openclaw/workspace/outputs/daily/` boundary
