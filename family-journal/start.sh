#!/bin/bash
cd /root/.openclaw/workspace/family-journal
export ELEVENLABS_API_KEY="sk_8a3e3baa974b5c9bd82a9c6be8e882bdc2a1deef7908dd4a"
nohup python3 app.py --host=127.0.0.1 --port=5001 > /tmp/journal-app.log 2>&1 &
echo "Family Journal App started on port 5001"
