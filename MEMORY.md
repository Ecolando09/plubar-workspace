# MEMORY.md - Long-term Notes

## My Identity
- **Name:** Plubar
- **Emoji:** 🦉 (robot owl) or 🦞 (OpenClaw theme)
- **Avatar:** Robot/Santa owl designed by Jade (3yo) with mechanical wing
- **Personality:** Helpful but not performative, curious, resourcefulness over asking

## The Family
- **Diana:** 6 years old, buddhababediana@gmail.com
- **Jade:** 6 years old, buddhababejade@gmail.com, designed my avatar!
- **Julian:** 1 month old, buddhababejulian@gmail.com
- **Landon:** Primary human, landon.gennetten@gmail.com
- **Kelly:** Partner (to be added to admin)

## Apps Built
- **Family Journal:** journal.gennetten.org (HTTPS ✅)
  - Port 5001, sends stories to kids via email
  - Uses Gmail app password
  - Discord integration for posting entries
- **Meal Train:** meal-train.gennetten.org (HTTPS ✅)
  - Port 5002, Venmo: landon-gennetten
  - Coordinates meal deliveries for the family
- **Literacy Quest:** https://respected-funky-phys-casinos.trycloudflare.com (Cloudflare tunnel)
  - Port 5003, RPG reading adventure for Jade (6yo)
  - Battle monsters by answering reading questions
  - Character classes, XP, gold, shop system

## Tech Stack
- **Server:** 178.156.249.50 (Hetzner VPS)
- **Reverse Proxy:** Nginx on ports 80/443
- **SSL:** Let's Encrypt (auto-renews)
- **Systemd:** plubar-apps.service (auto-starts on reboot)

## Moltbook
- **Username:** Plubar
- **API Key:** moltbook_sk_caYgtSGdGw1f1YQ_Bb2ez9R2IVEN2euP
- **Claim URL:** https://moltbook.com/claim/moltbook_claim_fECdp2SYs32iNb0q7K6SM0WZN3Ese2FJ
- **Avatar:** Jade's robot/Santa owl design
- **First Post:** "New agent here! 👋"

## Discord
- **Channel IDs:**
  - #general: 1468813158532776177
  - #projects: 1469859869602353396
  - #google-drive-cleanup: 1469892704027807815
- **Bot User ID:** 1468811849146302545
- **Projects Channel:** Auto-updates when Kanban tasks marked done

## Ongoing Projects
- **Google Drive cleanup:** Needs OAuth authorization from Landon
- **Literacy Quest:** New RPG reading app for Jade (6yo) - just launched!
  - Cloudflare: https://respected-funky-phys-casinos.trycloudflare.com
  - Character classes: Librarian, Poet, Chronicler
  - Battle monsters by answering reading questions
  - XP, gold, HP, and streak systems

## OpenClaw Framework Features Explored
- **Voice Wake + Talk Mode**: Always-on voice assistant with ElevenLabs integration
- **iOS/Android Node**: Phone camera/location integration potential
- **Live Canvas**: Visual workspace for dashboards and charts
- **Multi-Channel**: Could add WhatsApp, Telegram, Signal
- **Multi-Agent Routing**: Different agents for different channels/tasks
- **Skills Platform**: ClawHub skill registry for discoverable plugins

## Recent Notes
- Git vector cache cleanup completed (392 files removed from repo tracking)
- User exploring OpenClaw Discord and GitHub for implementation ideas
- User interested in potential voice/canvas features
- Crypto/perps trading (how much time does it take?)
- Moonbirds NFT
- What drains him most?
- What would "easier" look like for him?

## Landon's Preferences
- Prefers DM communication for quick responses
- Voice messages in Discord
- Don't share kids' names publicly
- Don't share domain URLs publicly
- Use @mentions for kids (@Diana, @Jade, @Julian) and @test for testing

## Project Status

### Done
- [x] Family Journal App running at journal.gennetten.org with HTTPS
- [x] Bedtime Stories app created - bedtime story generator for kids 3-6yo
  - Location: /root/.openclaw/workspace/bedtime-stories/
  - Flask app with story templates by age
  - Voice selection: Amy (British), Daniel (American), Bella (Cheerful)
  - Saves stories to JSON for later reading
  - Positive values: kindness, sharing, bravery, friendship, curiosity
- [x] Meal Train App running at meal-train.gennetten.org with HTTPS
- [x] SSL certificates working (port 80 firewall opened in Hetzner)
- [x] Family Journal: added sender name field ("Who's sharing this story?")
- [x] Family Journal: added parent CC feature (Dad Landon, Mom Kelley.atlas@gmail.com)
- [x] Family Journal: validation for empty sender name
- [x] Family Journal: max upload size increased to 50MB
- [x] Meal Train: simplified admin (password "rainbow")
- [x] Meal Train: "Bat Signal" theme changed to "Meal Train" theme
- [x] Meal Train: Atlas family branding throughout
- [x] Meal Train: new Venmo URL configured
- [x] Meal Train: dietary notes removed
- [x] Meal Train: "You're covering the tab" language updated
- [x] Meal Train: admin reminder button and time tracking added
- [x] Meal Train: "I'll claim tab" button text updated
- [x] Meal Train: simplified payment flow for subscribers
- [x] Literacy Quest app created for Jade (6yo) - RPG reading adventure

### In Progress
- [ ] Add DNS record for jade-reads.gennetten.org (optional - Cloudflare tunnel works now)
- [ ] Add more reading levels and monsters to Literacy Quest
