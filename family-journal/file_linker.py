#!/usr/bin/env python3
"""
File Linker - Self-hosted file link system.
Files are stored once, links redirect anywhere.
"""

import os
import json
import random
import string
from datetime import datetime

LINKS_FILE = os.path.join(os.path.dirname(__file__), 'file_links.json')

def load_links():
    """Load file links from JSON."""
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_links(links):
    """Save file links to JSON."""
    with open(LINKS_FILE, 'w') as f:
        json.dump(links, f, indent=2)

def generate_short_code(length=8):
    """Generate a random short code."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def create_link(filepath, redirect_url=None):
    """Create a new file link."""
    links = load_links()
    
    # Generate unique short code
    short_code = generate_short_code()
    while short_code in links:
        short_code = generate_short_code()
    
    # Store link data
    links[short_code] = {
        'filepath': filepath,
        'redirect_url': redirect_url,
        'created_at': datetime.now().isoformat(),
        'original_filename': os.path.basename(filepath)
    }
    
    save_links(links)
    return short_code

def get_link(short_code):
    """Get file link data."""
    links = load_links()
    return links.get(short_code)

def update_redirect(short_code, new_redirect_url):
    """Update where a link redirects to (for moving files)."""
    links = load_links()
    if short_code in links:
        links[short_code]['redirect_url'] = new_redirect_url
        links[short_code]['updated_at'] = datetime.now().isoformat()
        save_links(links)
        return True
    return False

def delete_link(short_code):
    """Delete a file link."""
    links = load_links()
    if short_code in links:
        del links[short_code]
        save_links(links)
        return True
    return False

def list_links():
    """List all file links."""
    return load_links()

def get_all_short_codes():
    """Get all short codes for batch updates."""
    return list(load_links().keys())
