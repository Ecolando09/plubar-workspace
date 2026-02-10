#!/usr/bin/env python3
"""
Google Drive Integration Setup Wizard
Interactive setup for Family Journal Google Drive integration.
"""

import os
import sys
import json
from pathlib import Path

SETUP_LOG = []


def log(msg, type="info"):
    """Log a message."""
    emoji = {"info": "📝", "success": "✅", "error": "❌", "tip": "💡", "step": "🔧"}
    print(f"  {emoji.get(type, '📝')} {msg}")
    SETUP_LOG.append(f"[{type.upper()}] {msg}")


def check_python_packages():
    """Check if required packages are installed."""
    log("Checking Python packages...", "step")
    
    required = ['google-auth', 'google-auth-oauthlib', 'google-auth-httplib2', 'google-api-python-client']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            log(f"  {package} ✅", "success")
        except ImportError:
            missing.append(package)
            log(f"  {package} ❌", "error")
    
    if missing:
        log("Installing missing packages...", "step")
        for pkg in missing:
            os.system(f"pip3 install {pkg} > /dev/null 2>&1")
            log(f"  Installed {pkg}", "success")
    
    return True


def check_environment():
    """Check current environment variables."""
    log("Checking environment...", "step")
    
    env_vars = {
        'GOOGLE_CLIENT_ID': None,
        'GOOGLE_CLIENT_SECRET': None,
        'GOOGLE_REFRESH_TOKEN': None,
        'GOOGLE_DRIVE_FOLDER_ID': None
    }
    
    for var in env_vars:
        value = os.environ.get(var)
        env_vars[var] = value
        if value:
            log(f"  {var[:20]}... ✅", "success")
        else:
            log(f"  {var[:20]}... ❌ (not set)", "error")
    
    return env_vars


def create_credentials_template():
    """Create credentials template file."""
    log("Creating credentials template...", "step")
    
    template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost:8080/callback"]
        }
    }
    
    creds_file = os.path.join(os.path.dirname(__file__), 'credentials.json')
    
    with open(creds_file, 'w') as f:
        json.dump(template, f, indent=2)
    
    log(f"  Created: {creds_file}", "success")
    return creds_file


def create_env_file(env_vars):
    """Create .env file with environment variables."""
    log("Creating .env file...", "step")
    
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    # Read existing if exists
    existing = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, val = line.strip().split('=', 1)
                    existing[key] = val
    
    # Merge with env vars
    all_vars = {
        'GOOGLE_CLIENT_ID': env_vars.get('GOOGLE_CLIENT_ID', ''),
        'GOOGLE_CLIENT_SECRET': env_vars.get('GOOGLE_CLIENT_SECRET', ''),
        'GOOGLE_REFRESH_TOKEN': env_vars.get('GOOGLE_REFRESH_TOKEN', ''),
        'GOOGLE_DRIVE_FOLDER_ID': env_vars.get('GOOGLE_DRIVE_FOLDER_ID', '')
    }
    
    # Keep existing values if new ones are empty
    for key in all_vars:
        if not all_vars[key] and key in existing:
            all_vars[key] = existing[key]
    
    with open(env_file, 'w') as f:
        f.write("# Google Drive Integration\n")
        for key, val in all_vars.items():
            f.write(f"{key}={val}\n")
    
    log(f"  Created: {env_file}", "success")
    return env_file


def create_readme():
    """Create README for Google Drive integration."""
    log("Creating README...", "step")
    
    readme = '''# Google Drive Integration for Family Journal

## Quick Setup

### 1. Get OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Family Journal")
3. Enable Google Drive API:
   - Navigate to APIs & Services > Library
   - Search for "Google Drive API"
   - Click Enable
4. Create OAuth credentials:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop application"
   - Download the JSON file
5. Save the JSON file as `google_drive/credentials.json`

### 2. Get Refresh Token

Run the token script:
```bash
cd /root/.openclaw/workspace/family-journal/google_drive
python3 get_token.py
```

This opens a browser for OAuth consent. After authorizing, your refresh token is saved.

### 3. Configure Environment

Set these environment variables or add to `.env`:
```bash
export GOOGLE_CLIENT_ID="your_client_id"
export GOOGLE_CLIENT_SECRET="your_client_secret"
export GOOGLE_REFRESH_TOKEN="your_refresh_token"
export GOOGLE_DRIVE_FOLDER_ID="your_folder_id"
```

### 4. Create a Folder (Optional)

Create a folder in Google Drive for journal entries and copy its ID from the URL.

## Usage

### Command Line Upload

```bash
cd /root/.openclaw/workspace/family-journal/google_drive
python3 uploader.py /path/to/video.mp4
```

### In Family Journal

The app automatically uses Google Drive for files > 25MB.

## Troubleshooting

### "credentials.json not found"
Download OAuth credentials from Google Cloud Console and save as `google_drive/credentials.json`.

### "access_denied" or "invalid_client"
- Make sure Google Drive API is enabled
- Check that OAuth consent is configured
- Verify client_id and client_secret are correct

### "token expired"
Run `python3 get_token.py` again to refresh your token.

## File Structure

```
family-journal/
├── google_drive/
│   ├── __init__.py
│   ├── uploader.py         # Main upload module
│   ├── get_token.py        # Get OAuth refresh token
│   ├── setup.py            # This setup wizard
│   ├── credentials.json    # OAuth credentials (create from template)
│   └── token.json          # Generated on first run
├── .env                    # Environment variables
└── ...
```
'''
    
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    
    with open(readme_file, 'w') as f:
        f.write(readme)
    
    log(f"  Created: {readme_file}", "success")
    return readme_file


def main():
    """Run the setup wizard."""
    print("\n" + "="*60)
    print("  📁 Google Drive Integration Setup")
    print("  Family Journal App")
    print("="*60)
    print()
    
    # Check packages
    check_python_packages()
    print()
    
    # Check environment
    env_vars = check_environment()
    print()
    
    # Create files
    create_credentials_template()
    print()
    
    # Create README
    create_readme()
    print()
    
    # Summary
    print("="*60)
    print("  📋 Setup Summary")
    print("="*60)
    print()
    
    if not env_vars.get('GOOGLE_CLIENT_ID'):
        print("⚠️  Not fully configured yet!")
        print()
        print("To complete setup:")
        print("  1. Get OAuth credentials from Google Cloud Console")
        print("  2. Save them to google_drive/credentials.json")
        print("  3. Run: python3 get_token.py")
        print("  4. Add environment variables to .env")
    else:
        print("✅ Google Drive is configured!")
        print()
        print("To upload a test file:")
        print("  cd /root/.openclaw/workspace/family-journal/google_drive")
        print("  python3 uploader.py /path/to/file.mp4")
    
    print()
    print("="*60)
    
    return True


if __name__ == '__main__':
    main()
