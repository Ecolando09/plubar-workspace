# Morning Briefing Skill

Generate daily morning briefing with weather, crypto prices, AI news, and BIRB alerts.

## Description

Produces a comprehensive morning briefing combining:
- Weather (from Open-Meteo API)
- Crypto prices (Moonbirds/BIRB)
- AI news (Wizdom)
- BIRB price alerts (>10% movement)

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

- requests (weather, prices)
- python-dateutil
- Output templates in `skills/morning-briefing/templates/`

## Notes

- Runs automatically via cron at 8AM EST
- Combines output from `birb-tracker` and `wizdom-summary`
- Templates loaded from skill folder (not embedded)
- Outputs to `/root/.openclaw/workspace/outputs/daily/` boundary
