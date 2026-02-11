#!/usr/bin/env python3
"""Fix Google Drive tokens by converting authorized_tokens.json to token.json"""

import json
import os

def main():
    auth_tokens_path = os.path.join(os.path.dirname(__file__), 'authorized_tokens.json')
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')

    if not os.path.exists(auth_tokens_path):
        print(f"Error: {auth_tokens_path} not found")
        return False

    with open(auth_tokens_path) as f:
        auth_tokens = json.load(f)

    # Create proper token.json format
    token_data = {
        'access_token': auth_tokens.get('token', ''),
        'refresh_token': auth_tokens.get('refresh_token', ''),
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': auth_tokens.get('client_id', ''),
        'client_secret': auth_tokens.get('client_secret', ''),
    }

    with open(token_path, 'w') as f:
        json.dump(token_data, f, indent=2)

    print(f"Created {token_path}")
    return True

if __name__ == '__main__':
    main()
