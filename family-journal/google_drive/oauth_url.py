#!/usr/bin/env python3
"""
Google OAuth with Local Server
Starts a server on port 8080 to handle the OAuth redirect.
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
import sys

REDIRECT_URI = "http://localhost:8080/callback"
AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/callback':
            query = parse_qs(parsed.query)
            if 'code' in query:
                code = query['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write('<html><body><h1>Authorization Successful!</h1><p>Check your terminal!</p></body></html>'.encode())
                with open('.oauth_code', 'w') as f:
                    f.write(code)
                global code_received
                code_received = code
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def get_credentials():
    with open('credentials.json', 'r') as f:
        creds = json.load(f)
    if 'installed' in creds:
        return creds['installed']['client_id'], creds['installed']['client_secret']
    elif 'web' in creds:
        return creds['web']['client_id'], creds['web']['client_secret']
    raise ValueError("Unknown credentials format")

def main():
    global code_received
    code_received = None
    
    print("\n" + "="*60)
    print("  Google OAuth")
    print("="*60)
    
    try:
        CLIENT_ID, CLIENT_SECRET = get_credentials()
        print("\nCredentials loaded")
    except Exception as e:
        print(f"\nError: {e}")
        return
    
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'https://www.googleapis.com/auth/drive.file',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = AUTH_URL + '?' + urllib.parse.urlencode(params)
    
    print("\nOpening browser for authorization...")
    print(f"\nURL: {auth_url[:80]}...\n")
    
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    webbrowser.open(auth_url)
    
    print("Waiting for authorization (complete it in your browser)...\n")
    
    timeout = 120
    start = time.time()
    
    while code_received is None and (time.time() - start) < timeout:
        server.handle_request()
        time.sleep(0.5)
    
    if code_received:
        print(f"Code received: {code_received[:30]}...")
        import requests
        data = {
            'code': code_received,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        response = requests.post(TOKEN_URL, data=data)
        if response.status_code == 200:
            token_data = response.json()
            with open('token.json', 'w') as f:
                json.dump(token_data, f, indent=2)
            print(f"\nToken saved to token.json")
            print(f"Access token: {token_data.get('access_token', 'N/A')[:20]}...")
        else:
            print(f"\nToken error: {response.text}")
    else:
        print("\nTimeout - authorization not completed")
    
    server.server_close()

if __name__ == '__main__':
    import urllib.parse
    main()
