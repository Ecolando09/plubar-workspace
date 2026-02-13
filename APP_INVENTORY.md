# 📱 Plubar's App Inventory

## Running Apps

| App Name | Port | Local URL | Public URL | Notes |
|----------|------|-----------|------------|-------|
| Family Journal | 5001 | http://localhost:5001 | journal.gennetten.org (via Nginx) | 📖 Story sharing for kids |
| Meal Train | 5002 | http://localhost:5002 | meal-train.gennetten.org (via Nginx) | 🚂 Meal coordination |
| Literacy Quest / Jade Reads | 5003 | http://localhost:5003 | jade.gennetten.org (planned) | 🎮 RPG reading game |
| Bedtime Stories | 5004 | http://localhost:5004 | Via Cloudflare tunnel | 🌙 Story generator with voice |
| Crypto Tax Tracker | 5005 | http://localhost:5005 | ready-mary-sydney-cumulative.trycloudflare.com | 💰 Tax calculations |

## Access Commands

```bash
# Check if app is running
lsof -i :<port>

# View logs
tail -f /tmp/<app-name>.log

# Restart app
cd /root/.openclaw/workspace/<app-folder>
pkill -f "<app-name>"
python3 app.py &
```

## Tunnels & Proxies

### Cloudflare Tunnels (temporary)
- **Crypto Tax**: `ready-mary-sydney-cumulative.trycloudflare.com`

### Nginx Reverse Proxy (permanent domains)
- **Family Journal** → journal.gennetten.org (HTTPS)
- **Meal Train** → meal-train.gennetten.org (HTTPS)

## Systemd Services (if configured)
- `family-journal.service`
- `meal-train.service`
- `literacy-quest.service`
- `bedtime-stories.service`
- `telegram-bridge.service`

## Adding New Apps

To add a new app to this inventory:
1. Update this table
2. Add to running services check
3. Configure Nginx or Cloudflare tunnel if needed
4. Document port and access method

Last Updated: 2026-02-12
