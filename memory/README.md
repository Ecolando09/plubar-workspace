# Continuous Memory System for OpenClaw

Based on innovations from @ecolando's context transfer system.

## Overview

This system maintains continuous memory across OpenClaw session compactions by:

1. **Hourly Summarization** - Captures activity every hour
2. **Pre-Compaction Dumps** - Saves recent state before compaction
3. **Vector Memory Search** - Semantic search over memories
4. **Prompt Hook** - Injects relevant memories before processing

## Components

### hourly_summarizer.py
Summarizes recent session activity and appends to daily memory file.
- Run: `python3 /root/.openclaw/workspace/memory/hourly_summarizer.py`
- Schedule: `0 * * * *` (hourly)

### precompact_dump.py
Saves recent conversation state before compaction.
- Run: `python3 /root/.openclaw/workspace/memory/precompact_dump.py`
- Schedule: `*/30 * * * *` (every 30 min)

### prompt_hook.py
Injects relevant memories before processing user prompts.
- Usage: `python3 /root/.openclaw/workspace/memory/prompt_hook.py <prompt_file>`

### vector_search.py
Semantic search over memory files.
- Usage: `from vector_search import inject_memories_into_context`

### embed_memories.py
Embeds and indexes memories for semantic search.
- Run: `python3 /root/.openclaw/workspace/memory/embed_memories.py`
- Schedule: `0 */2 * * *` (every 2 hours)

## Cron Jobs Installed

```bash
# Hourly memory summarization
0 * * * * /usr/bin/python3 /root/.openclaw/workspace/memory/hourly_summarizer.py >> /root/.openclaw/workspace/memory/hourly.log 2>&1

# Pre-compaction dump every 30 minutes
*/30 * * * * /usr/bin/python3 /root/.openclaw/workspace/memory/precompact_dump.py >> /root/.openclaw/workspace/memory/precompact.log 2>&1

# Vector embedding job every 2 hours
0 */2 * * * /usr/bin/python3 /root/.openclaw/workspace/memory/embed_memories.py >> /root/.openclaw/workspace/memory/embed.log 2>&1
```

## Memory Files

- `/root/.openclaw/workspace/memory/YYYY-MM-DD.md` - Daily memory summaries
- `/root/.openclaw/workspace/memory/hourly/` - Hourly summary files
- `/root/.openclaw/workspace/memory/precompact/` - Pre-compaction dumps
- `/root/.openclaw/workspace/memory/vectors/` - Embedded memories

## Environment Variables

Optional:
- `OPENAI_API_KEY` - For embedding generation (falls back to keyword search if not set)

## How It Works

1. **During Normal Operation:**
   - Hourly summarizer captures activity
   - Pre-compaction dump saves state every 30 min
   - All sessions logged to JSONL files

2. **Before Compaction:**
   - Prompt hook activates
   - Extracts relevant memories via vector search
   - Injects memories into context

3. **After Compaction:**
   - Recent summaries injected with compact summary
   - Pre-compaction state restored
   - Vector memories available for search

## Testing

```bash
# Test hourly summarizer
python3 /root/.openclaw/workspace/memory/hourly_summarizer.py

# Test pre-compaction dump
python3 /root/.openclaw/workspace/memory/precompact_dump.py

# Test vector search
python3 /root/.openclaw/workspace/memory/vector_search.py

# Test prompt hook
echo "test query" | python3 /root/.openclaw/workspace/memory/prompt_hook.py

# Test embedding
python3 /root/.openclaw/workspace/memory/embed_memories.py
```

## Credits

Inspired by @ecolando's context transfer system for ClawdBot.
See: https://x.com/i/status/2020339935178567923
