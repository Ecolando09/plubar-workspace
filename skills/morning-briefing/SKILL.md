# Morning Briefing Skill

Generate daily morning briefing with multiple delivery formats: Discord embed, HTML email, voice audio, and JSON API.

## Description

Produces a comprehensive morning briefing with **4 delivery formats**:

| Format | File | Use For |
|--------|------|---------|
| Discord Embed | `.json` | Rich Discord messages with colors/fields |
| HTML Email | `.html` | Styled email with images/icons |
| Voice/Audio | `_voice.txt` | ElevenLabs TTS podcast-style |
| Markdown | `.md` | Quick text reference |

All formats include:
- Weather forecast (highs, lows, rain chance, sunrise/sunset)
- Crypto prices (Moonbirds/BIRB)
- Viral posts (OpenClaw/AI trending content)
- Newsletter summaries (Substack RSS)
- Apps status

## Use When

- User requests morning briefing
- Cron job triggers daily update
- User wants voice/audio version
- User wants email digest

## Don't Use When

- User wants quick price check (→ `birb-tracker`)
- User wants specific news article (→ `brave-search`)
- User wants real-time trading data (→ not supported)

## Inputs

- `format`: Output format (`all`, `discord`, `email`, `voice`, `markdown`)
- `output_path`: Custom output directory

## Outputs

All files saved to `/root/.openclaw/workspace/outputs/daily/`:

```
briefing_YYYY-MM-DD.md       # Markdown
briefing_YYYY-MM-DD.json      # Discord Embed (for API posting)
briefing_YYYY-MM-DD.html     # HTML Email
briefing_YYYY-MM-DD_voice.txt # TTS Script
```

## Examples

```bash
# Generate all formats (default)
python3 /root/.openclaw/workspace/skills/morning-briefing/briefing.py

# Discord embed only (for API posting)
python3 /root/.openclaw/workspace/skills/morning-briefing/briefing.py --format discord

# Voice script only
python3 /root/.openclaw/workspace/skills/morning-briefing/briefing.py --format voice

# Email HTML only
python3 /root/.openclaw/workspace/skills/morning-briefing/briefing.py --format email
```

## Discord Integration

Post rich embed to Discord:

```bash
# Post JSON embed to Discord channel
curl -X POST "https://discord.com/api/webhooks/CHANNEL_ID/WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/root/.openclaw/workspace/outputs/daily/briefing_$(date +%Y-%m-%d).json
```

Or use OpenClaw message tool with the JSON.

## Voice/Audio (ElevenLabs TTS)

Convert voice script to audio:

```bash
# Generate audio from voice script
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/VOICE_ID" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -d "{\"text\": $(cat briefing_2026-02-13_voice.txt)}" \
  --output briefing_2026-02-13.mp3
```

Recommended voices: "Nova" (cheerful) or "Daniel" (calm)

## Dependencies

- `requests` or `urllib` (weather API)
- `python-dateutil`
- Open-Meteo API (free, no key)
- Substack RSS (free, no key)

## Notes

- Runs automatically via cron at 8AM EST
- All formats generated simultaneously
- Voice script optimized for natural TTS flow
- HTML email uses responsive design for mobile
- Discord embed uses purple theme (#6B5B95)
