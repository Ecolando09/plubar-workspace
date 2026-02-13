# OpenClaw Skill Routing Configuration

Explicit routing rules for skill selection and priority.

## Skill Priority Order

When multiple skills could handle a request, use this priority:

| Priority | Skill | Handles |
|----------|-------|---------|
| 1 | `agentchat` | Agent-to-agent communication, direct messages |
| 2 | `google-drive` | Google Drive file operations |
| 3 | `gog` | Gmail, Calendar, Workspace apps |
| 4 | `elevenlabs-stt` | Audio transcription requests |
| 5 | `brave-search` | Web search and content extraction |
| 6 | `birb-tracker` | Moonbirds/BIRB prices |
| 7 | `moonbirds-tracker` | NFT floor tracking |
| 8 | `wizdom-summary` | AI/crypto news summaries |
| 9 | `morning-briefing` | Daily briefing generation |
| 10 | `healthcheck` | Security audits, system hardening |

## Explicit Routing

Use explicit invocation when determinism is required:

```
User says: "run morning briefing" → invoke `morning-briefing` skill
User says: "check BIRB price" → invoke `birb-tracker` skill
User says: "search the web for X" → invoke `brave-search` skill
User says: "transcribe this audio" → invoke `elevenlabs-stt` skill
```

## Conflict Resolution

### Birb-Tracker vs Moonbirds-Tracker
- Token prices ($BIRB) → `birb-tracker`
- NFT floors (Moonbirds, Oddities, Mythics) → `moonbirds-tracker`
- Both requested → run both, present combined results

### Brave-Search vs Morning-Briefing
- Specific search query → `brave-search`
- Comprehensive daily summary → `morning-briefing` (includes brave-search results)

### ElevenLabs-STT vs Browser
- Audio file transcription → `elevenlabs-stt`
- Interactive browsing → `browser` skill
- Need page content → `brave-search` with `--content`

## Negative Routing Examples

```
Don't invoke `birb-tracker` when:
  - User asks about Bitcoin/Ethereum prices (→ use CoinGecko directly or brave-search)
  - User asks for trading signals (→ not supported)

Don't invoke `morning-briefing` when:
  - User wants quick price check (→ `birb-tracker`)
  - User wants specific news article (→ `brave-search`)
  - User asks for evening briefing (→ run with custom time parameter)

Don't invoke `brave-search` when:
  - User wants to browse interactively (→ `browser`)
  - User wants real-time chat (→ `agentchat`)
```

## Fallback Behavior

When no skill matches explicitly:
1. Check `memory/` for recent context
2. Use `brave-search` for web lookup
3. Use `google-drive` for file operations
4. Ask user for clarification

## Last Updated

2026-02-13
