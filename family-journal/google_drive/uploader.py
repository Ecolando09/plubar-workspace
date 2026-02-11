import os
import json
import time
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, HttpRequest
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveUploader:
    def __init__(self, credentials_file=None, token_file=None, folder_id=None):
        self.credentials_file = credentials_file or os.path.join(os.path.dirname(__file__), 'credentials.json')
        self.token_file = token_file or os.path.join(os.path.dirname(__file__), 'token.json')
        self.creds = None
        self.service = None
        self.folder_id = folder_id or os.environ.get('GOOGLE_DRIVE_FOLDER_ID', None)
        self.timeout = 1800
    
    def authenticate(self):
        self.creds = None
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                self.creds = Credentials(
                    token=token_data.get('access_token', ''),
                    refresh_token=token_data.get('refresh_token', ''),
                    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=token_data.get('scope', '').split() if token_data.get('scope') else None
                )
                if self.creds.expired or not self.creds.valid:
                    if self.creds.refresh_token:
                        self.creds.refresh(Request())
                        self._save_token()
                    else:
                        self.creds = None
            except Exception as e:
                print(f"Token error: {e}")
                self.creds = None
        
        if not self.creds or not self.creds.valid:
            if os.path.exists(self.credentials_file):
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                self.creds = flow.run_local_server(port=0)
            else:
                raise FileNotFoundError(f"Credentials not found: {self.credentials_file}")
            if self.creds:
                self._save_token()
        
        self.service = build('drive', 'v3', credentials=self.creds)
        return self
    
    def _save_token(self):
        token_data = {
            'access_token': self.creds.token,
            'refresh_token': self.creds.refresh_token,
            'token_uri': self.creds.token_uri,
            'client_id': self.creds.client_id,
            'client_secret': self.creds.creds.client_secret if hasattr(self.creds, 'client_secret') else '',
            'scope': ' '.join(self.creds.scopes) if self.creds.scopes else '',
            'expiry': self.creds.expiry.isoformat() if self.creds.expiry else ''
        }
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
    
    def _get_or_create_folder(self, folder_name, parent_id=None):
        """Get or create a folder."""
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(q=query, fields='files(id, name)').execute()
        
        if results.get('files'):
            return results['files'][0]['id']
        
        # Create folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = self.service.files().create(body=file_metadata, fields='id').execute()
        return folder['id']
    
    def count_entries_for_date(self, date_str):
        """Count how many entry folders exist for a given date."""
        if not self.service:
            self.authenticate()
        
        # Look for date folder
        date_folder_query = f"name='{date_str}' and mimeType='application/vnd.google-apps.folder' and '{self.folder_id}' in parents"
        date_results = self.service.files().list(q=date_folder_query, fields='files(id, name)').execute()
        
        if not date_results.get('files'):
            return 0
        
        date_folder_id = date_results['files'][0]['id']
        
        # Count entry subfolders (format: "Entry #N")
        entry_query = f"'{date_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and name contains 'Entry'"
        entry_results = self.service.files().list(q=entry_query, fields='files(id, name)').execute()
        
        count = 0
        if entry_results.get('files'):
            for f in entry_results['files']:
                # Extract number from "Entry #N"
                name = f['name']
                if '#' in name:
                    try:
                        num = int(name.split('#')[-1].strip())
                        count = max(count, num)
                    except ValueError:
                        pass
        
        return count
    
    def upload_file(self, filepath, filename=None, folder_name=None):
        """Upload a file to Drive."""
        if not self.service:
            self.authenticate()
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        filename = filename or os.path.basename(filepath)
        
        if folder_name:
            # Create/use specific folder
            target_id = self._get_or_create_folder(folder_name, self.folder_id)
        else:
            target_id = self.folder_id
        
        file_metadata = {
            'name': filename,
            'mimeType': self._get_mime_type(filepath)
        }
        if target_id:
            file_metadata['parents'] = [target_id]
        
        media = MediaFileUpload(filepath, resumable=True, chunksize=1024*1024*8)
        
        request = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink,webContentLink,mimeType,size'
        )
        
        start_time = time.time()
        response = None
        
        try:
            while response is None:
                if time.time() - start_time > self.timeout:
                    raise TimeoutError(f"Upload timed out after {self.timeout}s")
                
                status, response = request.next_chunk()
                
                if status:
                    progress = int(status.progress() * 100)
                    elapsed = int(time.time() - start_time)
                    print(f"  Uploading: {progress}% ({elapsed}s)")
        
        except TimeoutError as e:
            print(f"  ❌ {e}")
            raise
        
        print(f"  ✅ Uploaded: {filename}")
        return {
            'id': response.get('id'),
            'name': response.get('name'),
            'webViewLink': response.get('webViewLink'),
            'webContentLink': response.get('webContentLink'),
            'mimeType': response.get('mimeType'),
            'size': response.get('size'),
            'folder_name': folder_name
        }
    
    def upload_and_share(self, filepath, filename=None, folder_name=None):
        """Upload and make shareable."""
        result = self.upload_file(filepath, filename, folder_name)
        
        if result.get('id'):
            share_link = self.make_shareable(result['id'])
            if share_link:
                result['shareLink'] = share_link
        
        return result
    
    def make_shareable(self, file_id, permission_type='anyone', role='reader'):
        """Make a file shareable."""
        if not self.service:
            self.authenticate()
        
        permission = {'type': permission_type, 'role': role}
        
        try:
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()
            
            file = self.service.files().get(fileId=file_id, fields='webViewLink').execute()
            return file.get('webViewLink')
        except HttpError as e:
            print(f"Permission error: {e}")
            return None
    
    def _get_mime_type(self, filepath):
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filepath)
        return mime_type or 'application/octet-stream'


def format_file_size(size_bytes):
    if not size_bytes:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python uploader.py <filepath> [filename] [folder_name]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    folder_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    uploader = GoogleDriveUploader()
    uploader.authenticate()
    
    print(f"\n📤 Uploading: {filepath}")
    result = uploader.upload_and_share(filepath, filename, folder_name)
    
    print(f"\n✅ Success!")
    print(f"   Name: {result['name']}")
    print(f"   Folder: {result.get('folder_name', 'Root')}")
    print(f"   Link: {result.get('shareLink')}")
