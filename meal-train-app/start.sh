#!/bin/bash
cd /root/.openclaw/workspace/meal-train-app
export GMAIL_APP_PASSWORD="jowyzwbkfhdeaotu"
export FLASK_SECRET_KEY="meal-train-secret-$(date +%s)"
nohup python3 app.py --host=127.0.0.1 --port=5002 > /tmp/meal-train-app.log 2>&1 &
echo "Meal Train App started on port 5002"
