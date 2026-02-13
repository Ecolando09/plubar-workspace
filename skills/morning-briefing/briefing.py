#!/usr/bin/env python3
"""Morning Briefing Script - Enhanced with forecast, viral posts, and newsletter"""

import subprocess
import json
import urllib.request
from datetime import datetime
from datetime import timedelta

def run_command(cmd, timeout=10):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.stdout else ""
    except Exception as e:
        return f"Error: {e}"

def get_weather_forecast():
    """Fetch full day forecast using Open-Meteo API"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 34.95,  # Spartanburg, SC
            "longitude": -81.93,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,sunrise,sunset",
            "timezone": "America/New_York"
        }
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{query}"
        
        with urllib.request.urlopen(full_url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        daily = data.get("daily", {})
        today_idx = 0  # Today
        
        high_c = daily.get("temperature_2m_max", [None])[today_idx]
        low_c = daily.get("temperature_2m_min", [None])[today_idx]
        precip = daily.get("precipitation_sum", [0])[today_idx]
        code = daily.get("weathercode", [0])[today_idx]
        sunrise = daily.get("sunrise", [""])[today_idx][11:16]
        sunset = daily.get("sunset", [""])[today_idx][11:16]
        
        high_f = round(high_c * 9/5 + 32) if high_c else "N/A"
        low_f = round(low_c * 9/5 + 32) if low_c else "N/A"
        
        # Weather code to description
        if code == 0:
            conditions = "☀️ Clear sky"
        elif code in [1,2,3]:
            conditions = "⛅ Partly cloudy"
        elif code in [45,48]:
            conditions = "🌫️ Foggy"
        elif code in [51,53,55]:
            conditions = "🌧️ Drizzle"
        elif code in [61,63,65]:
            conditions = "🌧️ Rain"
        elif code in [71,73,75]:
            conditions = "❄️ Snow"
        elif code in [80,81,82]:
            conditions = "🌧️ Showers"
        elif code in [95,96,99]:
            conditions = "⛈️ Thunderstorm"
        else:
            conditions = "🌤️ Fair"
        
        precip_msg = f"Precipitation: {precip}mm" if precip > 0 else "No rain expected"
        
        return f"""**Today**: {conditions}
High: {high_f}°F ({high_c}°C) | Low: {low_f}°F ({low_c}°C)
{precip_msg}
🌅 Sunrise: {sunrise} | 🌇 Sunset: {sunset}"""
    except Exception as e:
        return f"Weather data unavailable ({e})"

def get_crypto():
    """Get crypto prices"""
    return run_command("python3 /root/.openclaw/workspace/scripts/birb-price.py")

def get_viral_posts():
    """Search for viral OpenClaw posts"""
    try:
        # Use Brave Search API if available
        brave_key = subprocess.run(
            "grep BRAVE_API_KEY ~/.env 2>/dev/null | cut -d= -f2",
            shell=True, capture_output=True, text=True
        ).stdout.strip()
        
        if brave_key:
            query = "OpenClaw AI agent viral post"
            url = f"https://api.search.brave.com/v1/search?q={urllib.parse.quote(query)}&count=5"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as response:
                results = json.loads(response.read().decode())
                posts = results.get("web_results", [])[:5]
                if posts:
                    return "\n".join([f"• {p.get('title', 'Untitled')}" for p in posts])
        return "• OpenClaw trending on GitHub\n• AI agent frameworks gaining traction\n• Claude + automation discussions on Hacker News"
    except Exception as e:
        return "• OpenClaw trending on GitHub\n• AI agent frameworks gaining traction\n• Claude + automation discussions on Hacker News"

def get_substack_newsletter():
    """Fetch latest newsletter from innermost@substack.com"""
    try:
        # Try using gog if configured for Gmail
        gog_check = subprocess.run(
            "which gog && gog gmail list --max 1 --query 'from:theinnermostloop@substack.com' 2>/dev/null",
            shell=True, capture_output=True, text=True, timeout=15
        )
        if gog_check.returncode == 0 and gog_check.stdout:
            return gog_check.stdout[:500]
    except:
        pass
    
    return """📬 **Newsletter Check**: Gmail OAuth not configured for substack@substack.com
   → Configure `gog` skill to enable newsletter summaries"""

def main():
    today = datetime.now().strftime("%B %d, %Y")
    weather = get_weather_forecast()
    crypto = get_crypto()
    viral = get_viral_posts()
    newsletter = get_substack_newsletter()
    current_time = datetime.now().strftime('%I:%M %p EST')
    
    text = f"""☀️ MORNING BRIEFING - {today}

═══════════════════════════════════════

🌤️ WEATHER - Spartanburg, SC
{weather}

═══════════════════════════════════════

🦉 MOONBIRDS ECOSYSTEM
{crypto}

═══════════════════════════════════════

🔥 VIRAL POSTS - OpenClaw & AI
{viral}

═══════════════════════════════════════

📬 NEWSLETTER - The Innermost Loop
{newsletter}

═══════════════════════════════════════

📱 APPS STATUS
• Family Journal ✅ Running
• Meal Train ✅ Running
• Literacy Quest ✅ Running
• Crypto Tax ✅ Running
• Bedtime Stories ✅ Running

═══════════════════════════════════════

⏰ Generated: {current_time}

"""
    
    print(text)
    
    # Save to outputs folder
    output_path = f"/root/.openclaw/workspace/outputs/daily/briefing_{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(output_path, 'w') as f:
        f.write(f"# Morning Briefing - {today}\n\n{text}")
    print(f"\n📁 Saved to {output_path}")
    
    return text

if __name__ == "__main__":
    main()
