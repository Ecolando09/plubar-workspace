#!/usr/bin/env python3
"""
OAuth Setup Script for Google Drive - Server-side authentication
Run this once to authorize full Drive access for the Family Journal app.
"""
import json
import os
import sys
import threading
import http.server
import urllib.parse
from http.server import HTTPServer
from google_auth_oauthlib.flow import InstalledAppFlow

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'family-journal', 'google_drive', 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'family-journal', 'google_drive', 'token.json')
SCOPES = ['https://www.googleapis.com/auth/drive']
REDIRECT_URI = 'http://localhost:8080/callback'

class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        auth_code = None
        
        if '/callback' in self.path:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'code' in params:
                auth_code = params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body style="font-family:Arial;text-align:center;padding:50px;"><h2>Success!</h2><p>Close this tab.</p></body></html>')
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"No code")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_setup():
    global auth_code
    auth_code = None
    
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Credentials not found: {CREDENTIALS_FILE}")
        return False
    
    print("=" * 50)
    print("  Google Drive OAuth Setup")
    print("=" * 50)
    print()
    
    # Load and modify credentials for redirect URI
    with open(CREDENTIALS_FILE, 'r') as f:
        creds_data = json.load(f)
    
    original_redirects = creds_data['installed'].get('redirect_uris', [])
    if REDIRECT_URI not in original_redirects:
        creds_data['installed']['redirect_uris'].append(REDIRECT_URI)
    
    temp_creds = '/tmp/google_oauth_creds.json'
    with open(temp_creds, 'w') as f:
        json.dump(creds_data, f)
    
    # Start callback server
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    
    # Create flow
    flow = InstalledAppFlow.from_client_secrets_file(temp_creds, SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    print(f"📋 Step 1: On YOUR LOCAL computer (not server), create SSH tunnel:")
    print(f"   ssh -L 8080:localhost:8080 root@{YOUR_SERVER_IP}")
    print()
    print(f"📋 Step 2: Open this URL on your local browser:")
    print(f"   {auth_url}")
    print()
    print(f"📋 Step 3: After authorizing, the redirect will go to localhost:8080")
    print(f"   which your SSH tunnel will forward to this server.")
    print()
    print("⏳ Waiting for authorization...")
    
    thread.join(timeout=120)
    server.server_close()
    os.remove(temp_creds)
    
    if not auth_code:
        print("❌ No authorization code received (timeout or error)")
        return False
    
    print("🔄 Exchanging code for tokens...")
    
    # Get tokens
    flow.fetch_token(code=auth_code)
    credentials = flow.credentials
    
    # Save tokens
    token_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print(f"✅ Tokens saved to: {TOKEN_FILE}")
    print()
    
    # Verify
    print("🔍 Verifying Drive access...")
    from googleapiclient.discovery import build
    service = build('drive', 'v3', credentials=credentials)
    
    results = service.files().list(
        q="mimeType='application/vnd.google-apps.folder'",
        pageSize=5
    ).execute()
    
    print(f"✅ Connected! Found {len(results.get('files', []))} folders in your Drive")
    for f in results.get('files', [])[:3]:
        print(f"   - {f['name']}")
    
    return True

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_setup()
