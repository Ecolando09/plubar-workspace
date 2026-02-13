#!/bin/bash
# Memory compaction cron job - runs every 2 hours
cd /root/.openclaw/workspace
python3 memory/precompact_dump.py --compact 2>&1 | tee /tmp/compaction.log
