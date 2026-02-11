# Morning Briefing Configuration
# Edit this file to customize what appears in your daily briefing

# Data Sources to Include
SOURCES = {
    "crypto_prices": True,           # Moonbirds/Birb prices
    "weather": True,                 # Weather for Spartanburg, SC
    "weekly_wizdom": True,          # Discord #weekly-wizdom summary
    "ai_news": True,                # @alexwg Substack
    "crypto_twitter": True,         # Top crypto X posts
    "openclaw_news": True,          # OpenClaw viral posts
}

# Voice Settings
VOICE = {
    "enabled": True,               # Generate voice briefing
    "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Daniel (British)
}

# Delivery
DELIVERY = {
    "discord_dm": True,             # Send to Discord DM
    "save_audio": False,            # Save MP3 to disk
}

# Location for weather
WEATHER_LOCATION = "Spartanburg,SC"

# crypto tracked
CRYPTO_TOKENS = ["$BIRB", "MOONBIRDS"]
