# OpenClaw Compaction Rules

Guidelines for managing context window and conversation history during long runs.

## When to Compact

Compact conversation history when:
- **Turn count exceeds**: 30 messages (aggressive mode)
- **Token estimate exceeds**: 50% of context window
- **Explicit trigger**: `/compact` or `session compaction` mentioned
- **Automatic schedule**: Every 2 hours via cron (`compaction_cron.sh`)

## What to Preserve (Never Compress)

These files are critical context and must survive compaction:

### Core Identity
- `SOUL.md` - Agent personality and values
- `MEMORY.md` - Long-term learned preferences
- `USER.md` - Human user preferences and context
- `IDENTITY.md` - Agent identity (name, emoji, avatar)
- `AGENTS.md` - Agent instructions and conventions

### Active Projects
- Current app development work
- Open pull requests or branches
- In-progress feature development

### System Configuration
- `TOOLS.md` - Local notes (camera names, SSH aliases, etc.)
- Skill configurations in `skills/_internal/`
- `APP_INVENTORY.md` - Current app status

## What to Compress

These can be compacted or summarized:

### Raw Logs
- `memory/YYYY-MM-DD.md` - Daily raw logs
  - Keep: Key decisions, important events
  - Compress: Routine operations, minor updates

### Session Transcripts
- Historical session data
- Old conversation contexts

### Temporary Files
- Build artifacts
- Cache files
- Old output files (>7 days)

## Compaction Strategies

### Strategy 1: Daily Log Summarization
```
Before compaction:
  memory/2026-02-13.md (500 lines of raw logs)

After compaction:
  memory/2026-02-13.md (50 lines of key events)
  memory/vectors/2026-02-13.md.json (embedded for recall)
```

### Strategy 2: Memory Extraction
Extract learnings to `MEMORY.md`:
```markdown
## 2026-02-13 Summary
- User prefers concise responses
- Added crypto-tax-app to portfolio
- Fixed Git push with SSH authentication
- Created BIRB tracker skill
```

### Strategy 3: Vector Embedding
For long-term recall without context bloat:
- Embed significant memories to `memory/vectors/`
- Use semantic search to retrieve when needed
- Keep embeddings permanently, delete originals

## Compaction Output

After compaction, save summary to `memory/compaction_history.md`:
```markdown
## Compaction: 2026-02-13 04:00 UTC
- Turns processed: 150
- Tokens saved: ~50,000
- Preserved: SOUL.md, MEMORY.md, USER.md
- Compressed: 5 daily logs
- Extracted: 3 new memory entries
```

## Manual Compaction

Trigger manual compaction:
```bash
python3 /root/.openclaw/workspace/memory/precompact_dump.py --compact
```

Review before committing:
```bash
cat /root/.openclaw/workspace/memory/precompact/precompact_YYYYMMDD_HHMM.json
```

## Best Practices

1. **Compact before context exhaustion** - Don't wait until errors
2. **Preserve personality** - SOUL.md always survives
3. **Keep recent context** - Current project stays in working memory
4. **Extract learnings** - Update MEMORY.md during compaction
5. **Version history** - Keep compaction history for debugging

## Emergency Compaction

If session errors due to context overflow:
1. Immediately compact oldest logs
2. Preserve only SOUL.md, USER.md, MEMORY.md
3. Restart session with compacted context
4. Restore from `memory/vectors/` as needed

## Semantic Memory Search

Before answering questions about prior work, always:
```bash
# Search semantic memory
/memory_search query: "your question"

# Get only relevant lines
/memory_get path: MEMORY.md lines: 10 from: 50
```

This loads only relevant context instead of entire files.

## Last Updated

2026-02-13
