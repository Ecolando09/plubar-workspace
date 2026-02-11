#!/usr/bin/env python3
"""Morning Briefing Script - Optimized with real data"""

import subprocess
import json
from datetime import datetime

def run_command(cmd, timeout=5):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.stdout else ""
    except:
        return ""

def get_weather():
    """Fetch actual weather data using Open-Meteo API (free, no key needed)"""
    # Spartanburg, SC coordinates: 34.95, -81.93
    try:
        result = subprocess.run(
            'timeout 5 curl -s "https://api.open-meteo.com/v1/forecast?latitude=34.95&longitude=-81.93&current_weather=true"',
            shell=True, capture_output=True, text=True, timeout=10
        )
        if result.stdout:
            data = json.loads(result.stdout)
            w = data.get("current_weather", {})
            temp_c = w.get("temperature", "N/A")
            temp_f = round(temp_c * 9/5 + 32) if isinstance(temp_c, (int, float)) else "N/A"
            wind = w.get("windspeed", "N/A")
            return f"Temperature: {temp_c}°C ({temp_f}°F), Wind: {wind}km/h"
    except Exception as e:
        pass
    return "Data unavailable"

def get_crypto():
    """Get crypto prices"""
    return run_command("python3 /root/.openclaw/workspace/scripts/birb-price.py")

def main():
    today = datetime.now().strftime("%B %d, %Y")
    weather = get_weather()
    crypto = get_crypto()
    current_time = datetime.now().strftime('%I:%M %p EST')
    
    text = f"""☀️ MORNING BRIEFING - {today}

═══════════════════════════════════════

🌤️ WEATHER - Spartanburg, SC
{weather}

═══════════════════════════════════════

🦉 MOONBIRDS ECOSYSTEM
{crypto}

═══════════════════════════════════════

⏰ Generated: {current_time}

"""
    
    print(text)
    return text

if __name__ == "__main__":
    main()
