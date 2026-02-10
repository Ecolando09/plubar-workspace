#!/usr/bin/env python3
"""
Get Google OAuth Refresh Token

This script helps you authenticate and get a refresh token for Google Drive API.
Run this once to set up your credentials.

Usage:
    python3 get_token.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from uploader import GoogleDriveUploader, SCOPES

def main():
    """Authenticate and save refresh token."""
    print("\n" + "="*60)
    print("  Google Drive OAuth Setup")
    print("="*60)
    
    # Check for credentials file
    credentials_file = os.path.join(os.path.dirname(__file__), 'credentials.json')
    
    if not os.path.exists(credentials_file):
        print("\n❌ credentials.json not found!")
        print("\nTo get credentials:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create a new project or select existing")
        print("  3. Enable Google Drive API")
        print("  4. Create OAuth 2.0 credentials (Desktop app)")
        print("  5. Download JSON and save as:")
        print(f"     {credentials_file}")
        print("\n📁 Saving credentials template...")
        
        # Create template
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
        
        with open(credentials_file, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"\n📝 Template saved to: {credentials_file}")
        print("   Edit it with your actual OAuth credentials!")
        return
    
    print("\n🔐 Starting OAuth authentication...")
    print("   A browser window will open for you to authorize.")
    print("   The refresh token will be saved automatically.\n")
    
    try:
        # This will open a browser and guide through OAuth flow
        uploader = GoogleDriveUploader()
        uploader.authenticate()
        
        print("\n✅ Authentication successful!")
        print(f"   Token saved to: {uploader.token_file}")
        
        # Check for folder ID
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if not folder_id:
            print("\n💡 Tip: Set GOOGLE_DRIVE_FOLDER_ID environment variable")
            print("   to automatically upload files to a specific folder.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. Google Drive API is enabled in Cloud Console")
        print("  2. OAuth credentials are configured correctly")
        print("  3. You're using valid client_id and client_secret")
        return
    
    # Test upload
    print("\n🧪 Testing upload...")
    test_file = '/tmp/test_upload.txt'
    with open(test_file, 'w') as f:
        f.write(f'Test file created at {datetime.now().isoformat()}\n')
    
    try:
        result = uploader.upload_file(test_file, 'OAuth Test File')
        print(f"\n✅ Test upload successful!")
        print(f"   File: {result['name']}")
        print(f"   Link: {result['webViewLink']}")
        
        # Clean up test file
        uploader.delete_file(result['id'])
        os.remove(test_file)
        
    except Exception as e:
        print(f"⚠️  Test upload failed: {e}")
    
    print("\n" + "="*60)
    print("  Setup Complete!")
    print("="*60)
    print("\n📋 Next steps:")
    print("  1. Set these environment variables:")
    print("     export GOOGLE_CLIENT_ID='your_client_id'")
    print("     export GOOGLE_CLIENT_SECRET='your_client_secret'")
    print("     export GOOGLE_REFRESH_TOKEN='your_refresh_token'")
    print("     export GOOGLE_DRIVE_FOLDER_ID='your_folder_id'")
    print("\n  2. Or add to /root/.openclaw/workspace/.env")
    print("\n🚀 Ready to upload files to Google Drive!")
    print()


if __name__ == '__main__':
    from datetime import datetime
    main()
