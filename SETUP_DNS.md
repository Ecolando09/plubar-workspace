# DNS & Hosting Setup for Plubar Apps

## Server Information

**Server IP:** `178.156.249.50`
**IPv6:** `2a01:4ff:f0:8eef::1`

## Required DNS Changes

Your dad needs to add these **A records** to the `gennetten.org` DNS zone:

### Option 1: A Records (Recommended)

```
journal.gennetten.org.  IN A  178.156.249.50
meal-train.gennetten.org. IN A  178.156.249.50
```

### Option 2: CNAME Records (if using a parent domain)

```
journal.gennetten.org.  IN CNAME  gennetten.org.
meal-train.gennetten.org. IN CNAME  gennetten.org.
```

Or if you have a wildcard:
```
*.gennetten.org.  IN A  178.156.249.50
```

## SSL/HTTPS Setup

I'll use certbot to automatically obtain free SSL certificates:

```bash
# For journal.gennetten.org
/usr/sbin/nginx -t && systemctl reload nginx
certbot --nginx -d journal.gennetten.org

# For meal-train.gennetten.org  
certbot --nginx -d meal-train.gennetten.org
```

## Running the Apps

### Family Journal App
```bash
cd /root/.openclaw/workspace/family-journal
./start.sh
# Runs on: http://127.0.0.1:5001
# Public: https://journal.gennetten.org
```

### Meal Train App
```bash
cd /root/.openclaw/workspace/meal-train-app
./start.sh
# Runs on: http://127.0.0.1:5002
# Public: https://meal-train.gennetten.org
```

## Nginx Reverse Proxy

Both apps are already configured behind nginx:
- `/etc/nginx/sites-available/journal.gennetten.org` → Family Journal (port 5001)
- `/etc/nginx/sites-available/meal-train.gennetten.org` → Meal Train (port 5002)

Nginx is running and proxying requests to the internal app ports.

## What to Tell Your Dad

> "I need you to add two A records to the gennetten.org DNS zone:
> 
> - `journal.gennetten.org` → `178.156.249.50`
> - `meal-train.gennetten.org` → `178.156.249.50`
> 
> Once the DNS propagates (usually 5-60 minutes), I'll run certbot to get free SSL certificates and the sites will be live at those URLs."

## Verification

After DNS is set up, verify with:
```bash
dig journal.gennetten.org +short
dig meal-train.gennetten.org +short
```

Both should return `178.156.249.50`.

## Files Created

- `/etc/nginx/sites-available/journal.gennetten.org`
- `/etc/nginx/sites-available/meal-train.gennetten.org`
- `/root/.openclaw/workspace/family-journal/start.sh`
- `/root/.openclaw/workspace/meal-train-app/start.sh`
