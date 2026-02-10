#!/usr/bin/env python3
"""
Discord-to-Family-Journal Bridge Integration

This script bridges Discord messages from the #family-journal channel to the 
Family Journal App by:
1. Downloading media attachments from Discord URLs
2. Parsing @mentions and #hashtags for kid tagging
3. Compiling stories from Discord messages
4. Sending emails to selected kids via SMTP

Features:
- Auto-detect @mentions (@Diana, @Jade, @Julian) and #hashtags (#Diana, #Jade, #Julian)
- Default to all kids if no mentions found
- TEST mode: emails landon.gennetten@gmail.com first before sending to kids

Usage:
    python discord_journal_bridge.py --message "Story text here" --attachments "url1,url2"
    python discord_journal_bridge.py --message "Hey @Diana check this out!" --test-mode
    python discord_journal_bridge.py --message "Hello #Jade and #Julian!" --kids "Diana,Jade"
"""

import os
import sys
import yaml
import requests
import argparse
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
import mimetypes

# Add the family-journal-app directory to path for imports
# family-journal and family-journal-app are sibling directories
APP_DIR = Path(__file__).parent
APP_LIB_DIR = APP_DIR.parent / "family-journal-app"
sys.path.insert(0, str(APP_LIB_DIR))

from email_sender import EmailSender


class DiscordJournalBridge:
    """Bridge for sending Discord messages to Family Journal as emailed stories."""
    
    # MIME type mapping for attachments
    MIME_MAP = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.mp4': 'video/mp4',
        '.mov': 'video/quicktime',
        '.avi': 'video/x-msvideo',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.m4a': 'audio/mp4',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
    }
    
    # Valid kid names (normalized for matching)
    VALID_KIDS = {'diana', 'jade', 'julian'}
    
    def __init__(self, config_path=None, test_mode=False):
        """Initialize the bridge with configuration.
        
        Args:
            config_path: Path to config.yaml
            test_mode: If True, emails landon.gennetten@gmail.com first before kids
        """
        if config_path is None:
            # Default: config.yaml in the same directory as this script
            config_path = APP_DIR / "config.yaml"
        
        self.config = self._load_config(config_path)
        self.uploads_dir = APP_DIR / "uploads"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.test_mode = test_mode
        
        # Initialize email sender
        email_config = self.config.get('email', {})
        self.sender_email = email_config.get('sender_email', '')
        self.email_sender = EmailSender(
            smtp_server=email_config.get('smtp_server', 'smtp.gmail.com'),
            smtp_port=email_config.get('smtp_port', 587),
            sender_email=self.sender_email,
            sender_password=email_config.get('sender_password', '')
        )
        
        # Build kid lookup from config
        self.kids = {}
        for kid in self.config.get('kids', []):
            name = kid.get('name', '')
            # Normalize name for matching (e.g., "Diana Atlas" -> "diana")
            normalized = name.lower().split()[0] if name else ''
            self.kids[name] = {
                'email': kid.get('email', ''),
                'emoji': kid.get('avatar_emoji', '👧'),
                'normalized': normalized
            }
        
        # Test mode recipient
        self.test_recipient = "landon.gennetten@gmail.com"
        
        print(f"✅ Discord Journal Bridge initialized")
        print(f"   - Config: {config_path}")
        print(f"   - Uploads dir: {self.uploads_dir}")
        print(f"   - Kids: {', '.join(self.kids.keys())}")
        if self.test_mode:
            print(f"   - 🧪 TEST MODE: Will email {self.test_recipient} before sending to kids")
    
    def _detect_kids_from_message(self, message_text):
        """
        Detect which kids are mentioned in the message using @mentions or #hashtags.
        
        Supports:
        - @Diana, @Jade, @Julian (Discord mentions)
        - #Diana, #Jade, #Julian (hashtags)
        - @test - Send to Landon for testing (overrides everything)
        
        Returns:
            list of kid names to include, or None for all kids, or ["__TEST__"] for test mode
        """
        if not message_text:
            return None
        
        import re
        text = message_text.lower()
        
        # Check for @test first - special mode for testing
        if '@test' in text.lower():
            return ["__TEST__"]
        
        detected = set()
        
        # Check for @mentions (Discord format: @Username)
        mentions = re.findall(r'@(\w+)', text, re.IGNORECASE)
        for mention in mentions:
            for kid_name, kid_info in self.kids.items():
                # Compare with normalized name (e.g., "Diana Atlas" -> "diana")
                if mention.lower() == kid_info.get('normalized', '').lower():
                    detected.add(kid_name)
        
        # Check for #hashtags
        hashtags = re.findall(r'#(\w+)', text, re.IGNORECASE)
        for tag in hashtags:
            for kid_name, kid_info in self.kids.items():
                # Compare with normalized name
                if tag.lower() == kid_info.get('normalized', '').lower():
                    detected.add(kid_name)
        
        # Return None if no mentions found (will default to all kids in send_to_kids)
        # Return list of detected kids if mentions found
        return list(detected) if detected else None
    
    def _load_config(self, config_path):
        """Load YAML configuration file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _guess_mime_type(self, url, filename):
        """Guess MIME type from URL or filename."""
        # Try to get from extension
        ext = Path(filename).suffix.lower()
        if ext in self.MIME_MAP:
            return self.MIME_MAP[ext]
        
        # Try mimetypes module
        mime, _ = mimetypes.guess_type(filename)
        if mime:
            return mime
        
        # Try to detect from URL content-type
        try:
            head_response = requests.head(url, allow_redirects=True, timeout=10)
            content_type = head_response.headers.get('Content-Type', '')
            if content_type:
                return content_type.split('/')[0] + '/' + content_type.split('/')[-1]
        except:
            pass
        
        return 'application/octet-stream'
    
    def _download_attachment(self, url, filename=None):
        """
        Download a file from URL to the uploads directory.
        
        Args:
            url: The URL to download from
            filename: Optional filename (extracted from URL if not provided)
        
        Returns:
            dict with 'path', 'filename', 'mime_type'
        """
        if filename is None:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or f"attachment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = os.urandom(4).hex()
        ext = Path(filename).suffix
        safe_name = f"{timestamp}_{unique_id}{ext}"
        
        filepath = self.uploads_dir / safe_name
        
        print(f"   📥 Downloading: {url}")
        print(f"   → Saving to: {filepath}")
        
        # Download the file
        try:
            response = requests.get(url, allow_redirects=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            mime_type = self._guess_mime_type(url, filename)
            print(f"   ✅ Downloaded ({mime_type}, {os.path.getsize(filepath)} bytes)")
            
            return {
                'path': str(filepath),
                'filename': safe_name,
                'mime_type': mime_type
            }
        except Exception as e:
            print(f"   ❌ Error downloading {url}: {e}")
            return None
    
    def compile_story(self, message_text, author_name="Someone", include_timestamp=True):
        """
        Compile Discord message into a story format.
        
        Args:
            message_text: The Discord message content
            author_name: Name of who posted the message
            include_timestamp: Whether to include timestamp
        
        Returns:
            HTML formatted story body
        """
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # Escape HTML and format the message
        import html
        safe_text = html.escape(message_text)
        
        # Convert URLs to clickable links
        import re
        url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
        safe_text = re.sub(url_pattern, r'<a href="\1">\1</a>', safe_text)
        
        # Format line breaks
        safe_text = safe_text.replace('\n', '<br>')
        
        story_html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 650px; margin: auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <div style="background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                <h1 style="color: #4A90D9; margin-bottom: 20px; text-align: center;">
                    📔 Family Journal Entry
                </h1>
                
                <div style="background: linear-gradient(90deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <p style="color: #333; font-size: 18px; line-height: 1.6; margin: 0;">
                        {safe_text}
                    </p>
                </div>
                
                <p style="color: #888; font-size: 14px; text-align: center; margin-top: 30px;">
                    Shared with love 💜
                    {"<br>📅 " + timestamp if include_timestamp else ""}
                </p>
            </div>
        </body>
        </html>
        """
        
        return story_html
    
    def send_to_kids(self, message_text, attachment_urls=None, kid_names=None, author_name="Discord", test_mode=False):
        """
        Main entry point: Download attachments, compile story, send emails.
        
        Args:
            message_text: The Discord message content
            attachment_urls: List of attachment URLs (comma-separated string or list)
            kid_names: List of kid names to send to (None = auto-detect from @mentions or #hashtags)
            author_name: Name of the Discord user who posted
            test_mode: If True, send to Landon instead of kids
        
        Returns:
            dict with success status and details
        """
        results = {
            'success': True,
            'attachments_downloaded': [],
            'emails_sent': [],
            'errors': []
        }
        
        # Auto-detect kids from @mentions if kid_names not specified or is default
        DEFAULT_RECIPIENTS = "Diana Atlas,Jade Atlas,Julian Atlas"
        if kid_names is None or kid_names == "" or kid_names == DEFAULT_RECIPIENTS:
            # Always check for @test first
            kid_names = self._detect_kids_from_message(message_text)
            if kid_names:
                if kid_names == ["__TEST__"]:
                    test_mode = True
                    print(f"\n🧪 Detected @test - sending to Landon for testing")
                else:
                    print(f"\n👀 Detected @mentions/hashtags: {', '.join(kid_names)}")
            elif not test_mode:
                # Default to all kids if no mentions found and not test mode
                kid_names = DEFAULT_RECIPIENTS
        
        # Parse attachment URLs
        if attachment_urls:
            if isinstance(attachment_urls, str):
                attachment_urls = [u.strip() for u in attachment_urls.split(',') if u.strip()]
            else:
                attachment_urls = [u.strip() for u in attachment_urls if u.strip()]
        
        # Download attachments
        attachments = []
        if attachment_urls:
            print(f"\n📥 Downloading {len(attachment_urls)} attachment(s)...")
            for url in attachment_urls:
                result = self._download_attachment(url)
                if result:
                    attachments.append(result)
                    results['attachments_downloaded'].append(url)
        
        # Compile story
        print(f"\n📝 Compiling story from Discord message...")
        story_html = self.compile_story(message_text, author_name)
        
        # Handle test mode
        if test_mode:
            # Get Landon's email from config or use default
            landon_email = self.config.get('email', {}).get('sender_email', 'landon.gennetten@gmail.com')
            recipients = ["Landon"]
            self.kids["Landon"] = {'email': landon_email, 'emoji': '👨‍👧‍👦'}
            print(f"\n🧪 TEST MODE: Sending to Landon ({landon_email})")
        else:
            # Determine recipients
            if kid_names is None:
                recipients = list(self.kids.keys())
            else:
                if isinstance(kid_names, str):
                    recipients = [k.strip() for k in kid_names.split(',') if k.strip()]
                else:
                    recipients = [k.strip() for k in kid_names if k.strip()]
        
        # Filter valid recipients
        valid_recipients = []
        for name in recipients:
            if name in self.kids:
                valid_recipients.append(name)
            else:
                print(f"   ⚠️ Unknown kid: {name}")
                results['errors'].append(f"Unknown recipient: {name}")
        
        if not valid_recipients:
            print(f"   ⚠️ No valid recipients found!")
            results['success'] = False
            results['errors'].append("No valid recipients")
            return results
        
        # Send emails
        print(f"\n📧 Sending story to {len(valid_recipients)} kid(s): {', '.join(valid_recipients)}")
        
        for kid_name in valid_recipients:
            kid_info = self.kids[kid_name]
            email = kid_info['email']
            emoji = kid_info['emoji']
            
            # Personalize the subject
            subject = f"🎉 New Family Journal Entry for You {emoji}"
            
            # Personalize the body with kid's name
            personalized_html = story_html.replace(
                'Shared with love 💜',
                f'Sent to {kid_name} {emoji} with love 💜'
            )
            
            print(f"   📤 Sending to {kid_name} ({email})...")
            
            try:
                success, msg = self.email_sender.send_story(
                    recipients=[email],
                    subject=subject,
                    body=personalized_html,
                    attachments=attachments
                )
                
                if success:
                    print(f"   ✅ Sent to {kid_name}")
                    results['emails_sent'].append({'name': kid_name, 'email': email})
                else:
                    print(f"   ❌ Failed: {msg}")
                    results['errors'].append(f"Failed to send to {kid_name}: {msg}")
                    results['success'] = False
            except Exception as e:
                print(f"   ❌ Error sending to {kid_name}: {e}")
                results['errors'].append(f"Error sending to {kid_name}: {str(e)}")
                results['success'] = False
        
        # Summary
        print(f"\n{'='*50}")
        print(f"📊 SUMMARY")
        print(f"{'='*50}")
        print(f"   Attachments downloaded: {len(results['attachments_downloaded'])}")
        print(f"   Emails sent successfully: {len(results['emails_sent'])}")
        if results['emails_sent']:
            for sent in results['emails_sent']:
                print(f"      - {sent['name']} → {sent['email']}")
        if results['errors']:
            print(f"   Errors: {len(results['errors'])}")
            for err in results['errors']:
                print(f"      - {err}")
        print(f"{'='*50}\n")
        
        return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Discord-to-Family-Journal Bridge',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect @mentions and #hashtags from message
  python discord_journal_bridge.py --message "Hey @Diana check this out!"
  
  # Send to all kids
  python discord_journal_bridge.py --message "Today was amazing!" --attachments "https://discord.com/files/123/photo.jpg"
  
  # Send to specific kids
  python discord_journal_bridge.py --message "Hello Diana and Jade!" --kids "Diana,Jade"
  
  # Message only, no attachments
  python discord_journal_bridge.py --message "Just a quick update today."
  
  # Multiple attachments
  python discord_journal_bridge.py --message "Check out these photos!" --attachments "url1.jpg,url2.png,url3.mp4"
  
  # TEST MODE: Send to Landon first before sending to kids
  python discord_journal_bridge.py --message "Testing the bridge!" --test-mode
        """
    )
    
    parser.add_argument('-m', '--message', required=True, help='Discord message text')
    parser.add_argument('-a', '--attachments', default='', help='Comma-separated list of attachment URLs')
    parser.add_argument('-k', '--kids', default=None, help='Comma-separated list of kid names (default: auto-detect)')
    parser.add_argument('-c', '--config', default=None, help='Path to config.yaml (default: family-journal/config.yaml)')
    parser.add_argument('-n', '--author', default='Discord', help='Author name for the story (default: Discord)')
    parser.add_argument('-t', '--test-mode', action='store_true', help='TEST MODE: Send to landon.gennetten@gmail.com first')
    
    args = parser.parse_args()
    
    # Initialize bridge
    bridge = DiscordJournalBridge(config_path=args.config, test_mode=args.test_mode)
    
    # Send to kids (or test recipient)
    results = bridge.send_to_kids(
        message_text=args.message,
        attachment_urls=args.attachments if args.attachments else None,
        kid_names=args.kids,
        author_name=args.author,
        test_mode=args.test_mode
    )
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
