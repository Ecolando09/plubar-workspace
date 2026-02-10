import json
import os
import yaml
import smtplib
import subprocess
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email import encoders
from mimetypes import guess_type
import secrets
import string

from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

with open('config.yaml') as f:
    config = yaml.safe_load(f)

app.config['MAX_CONTENT_LENGTH'] = config['app'].get('max_content_length', 524288000)
app.config['UPLOAD_FOLDER'] = config['app']['upload_folder']
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), exist_ok=True)

MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024

google_drive_available = False
try:
    from google_drive.uploader import GoogleDriveUploader
    google_drive_available = True
    print("Google Drive available")
except:
    print("Google Drive not available")

# Track entry numbers per day
ENTRY_COUNTER_FILE = 'entry_counter.json'

def get_entry_number():
    """Get the next entry number for today"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if os.path.exists(ENTRY_COUNTER_FILE):
        with open(ENTRY_COUNTER_FILE, 'r') as f:
            counters = json.load(f)
    else:
        counters = {}
    
    if counters.get('date') != today:
        counters = {'date': today, 'count': 0}
    
    counters['count'] += 1
    
    with open(ENTRY_COUNTER_FILE, 'w') as f:
        json.dump(counters, f)
    
    return counters['count']

def generate_video_thumbnail(filepath):
    """Generate a thumbnail from video using ffmpeg"""
    thumbnail_path = None
    try:
        # Generate unique thumbnail filename
        ext = os.path.splitext(filepath)[1]
        thumb_filename = f"thumb_{secrets.token_hex(8)}.jpg"
        thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', thumb_filename)
        
        # Extract frame at 1 second (or first frame if video is short)
        cmd = [
            'ffmpeg', '-y',
            '-ss', '1',
            '-i', filepath,
            '-vframes', '1',
            '-vf', 'scale=400:-1',
            '-q:v', '2',
            thumbnail_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(thumbnail_path):
            print(f"Generated thumbnail: {thumbnail_path}")
            return thumb_filename
        else:
            print(f"Thumbnail generation failed: {result.stderr.decode()[:200]}")
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
    
    return None

def get_link(filename):
    return filename[:6]

def create_link(filepath):
    code = get_link(os.path.basename(filepath))
    return code

@app.route('/')
def index():
    return render_template('index.html', 
                          kids_json=json.dumps(config.get('kids', [])),
                          kids=config.get('kids', []),
                          parents=config.get('parents', []))

@app.route('/upload-progress', methods=['POST'])
def upload_progress():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    print(f"Uploaded file: {filename} ({file_size / 1024 / 1024:.2f} MB)")
    
    # Generate thumbnail for videos
    thumbnail = None
    mime_type = guess_type(filename)[0]
    if mime_type and mime_type.startswith('video/'):
        print(f"Generating thumbnail for video: {filename}")
        thumbnail = generate_video_thumbnail(filepath)
        print(f"Thumbnail result: {thumbnail}")
    
    use_drive = google_drive_available and file_size >= MAX_ATTACHMENT_SIZE
    
    if use_drive:
        try:
            folder_id = config.get('app', {}).get('google_drive_folder_id')
            uploader = GoogleDriveUploader(folder_id=folder_id)
            uploader.authenticate()
        except Exception as e:
            print(f"Drive auth failed: {e}")
            use_drive = False
    
    if use_drive and google_drive_available:
        # Get entry number for naming the folder
        entry_num = get_entry_number()
        folder_name = f"Entry #{entry_num}"
        print(f"Uploading to Drive folder: {folder_name}")
        result = uploader.upload_and_share(filepath, filename=filename, folder_name=folder_name)
        print(f"Drive result: {result}")
        if result.get('shareLink'):
            os.remove(filepath)
            return jsonify({
                'status': 'uploaded',
                'filename': filename,
                'url': result['shareLink'],
                'size': file_size,
                'drive': True,
                'thumbnail': thumbnail
            })
        else:
            print(f"Drive upload succeeded but no share link. Keeping file local.")
            use_drive = False
    
    short_code = create_link(filepath)
    return jsonify({
        'status': 'uploaded',
        'filename': filename,
        'code': short_code,
        'size': file_size,
        'drive': False,
        'thumbnail': thumbnail
    })

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), filename)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        sender_name = request.form.get('sender_name', '').strip()
        story = request.form.get('story', '').strip()
        kids = request.form.getlist('kids')
        cc_parents = request.form.getlist('cc_parents')
        uploaded_files_json = request.form.get('uploaded_files', '[]')
        
        if not sender_name:
            return jsonify({'error': 'Sender name required'}), 400
        if not kids:
            return jsonify({'error': 'Select at least one child'}), 400
        if not story and not uploaded_files_json:
            return jsonify({'error': 'Story or files required'}), 400
        
        uploaded_files = json.loads(uploaded_files_json) if uploaded_files_json else []
        
        kid_emails = {}
        for kid in config.get('kids', []):
            if kid.get('email') in kids:
                kid_emails[kid['email']] = kid.get('name', '')
        
        if not kid_emails:
            return jsonify({'error': 'Invalid kid selection'}), 400
        
        parent_emails = []
        if cc_parents:
            for parent in config.get('parents', []):
                if parent.get('email') in cc_parents:
                    parent_emails.append(parent['email'])
        
        # Collect Drive links, thumbnails, and local files
        drive_links = []
        video_thumbnails = []  # Track videos with thumbnails
        image_attachments = []  # Track images separately
        other_attachments = []
        
        for f in uploaded_files:
            if f.get('drive') and f.get('url'):
                # Check if it's a video with thumbnail
                if f.get('thumbnail'):
                    video_thumbnails.append({
                        'url': f['url'],
                        'thumbnail': f['thumbnail'],
                        'filename': f.get('name', 'video')
                    })
                else:
                    drive_links.append({'url': f['url'], 'filename': f.get('name', 'file')})
            elif f.get('code'):
                code = f['code']
                for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                    if filename.startswith(code):
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        mime_type, _ = guess_type(filename)
                        maintype = mime_type.split('/')[0] if mime_type else 'application'
                        subtype = mime_type.split('/')[1] if mime_type else ''
                        
                        if maintype == 'image':
                            image_attachments.append(filepath)
                        elif 'video' in maintype or 'video' in subtype:
                            # Add link for local videos (when Drive share failed)
                            local_url = url_for('serve_file', filename=filename, _external=True)
                            if f.get('thumbnail'):
                                video_thumbnails.append({
                                    'url': local_url,
                                    'thumbnail': f['thumbnail'],
                                    'filename': f.get('name', 'video')
                                })
                            else:
                                drive_links.append({'url': local_url, 'filename': f.get('name', 'video')})
                        else:
                            other_attachments.append(filepath)
                        break
        
        # Calculate total image size
        total_image_size = sum(os.path.getsize(f) for f in image_attachments if os.path.exists(f))
        print(f"Total image size: {total_image_size / 1024 / 1024:.2f} MB")
        
        # Only attach images if total < 25MB
        MAX_IMAGES_SIZE = 25 * 1024 * 1024
        attach_images = total_image_size < MAX_IMAGES_SIZE
        
        # Build link text with date/time
        now = datetime.now()
        date_str = now.strftime('%B %d, %Y')
        time_str = now.strftime('%I:%M %p').lstrip('0')
        
        # Build HTML for Drive links
        links_html = ''
        for link_info in drive_links:
            links_html += f'<p><a href="{link_info["url"]}">📎 Check out this video taken on {date_str} at {time_str}</a></p>'
        
        # Build HTML for video thumbnails with overlay
        thumbnails_html = ''
        for video in video_thumbnails:
            thumb_url = f"/thumbnails/{video['thumbnail']}"
            thumbnails_html += f'''
            <div style="position: relative; display: inline-block; margin: 10px 5px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                <a href="{video["url"]}">
                    <img src="{thumb_url}" alt="{video["filename"]}" style="display: block; width: 200px; height: auto;">
                    <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-size: 16px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">▶ Click for video</span>
                    </div>
                </a>
            </div>
            '''
        
        # Send to each kid - create fresh message for each
        sent_count = 0
        send_errors = []
        
        for kid_email, kid_name in kid_emails.items():
            # Build email body for each recipient
            body_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
                <h1 style="color: #4A90D9;">📖 A Story Just For You!</h1>
                <p>{sender_name} just created a journal entry for you!</p>
                <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; white-space: pre-wrap;">{story}</div>
                {thumbnails_html}
                {links_html}
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Made with ❤️ by Family Journal
                </p>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('mixed')
            msg['Subject'] = f"📖 A Story from {sender_name}!"
            msg['From'] = f"{sender_name} <{config['email']['sender_email']}>"
            msg['To'] = kid_email
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            
            # Attach images if under limit
            if attach_images:
                for filepath in image_attachments:
                    try:
                        filename = os.path.basename(filepath)
                        mime_type, _ = guess_type(filename)
                        if not mime_type:
                            mime_type = 'application/octet-stream'
                        
                        with open(filepath, 'rb') as fp:
                            part = MIMEImage(fp.read(), _subtype=mime_type.split('/')[-1])
                            part.add_header('Content-Disposition', 'attachment', filename=filename)
                            msg.attach(part)
                        print(f"Attached image: {filename}")
                    except Exception as e:
                        print(f"Error attaching image {filepath}: {e}")
            
            # Attach other local files (audio, small videos)
            for filepath in other_attachments:
                try:
                    filename = os.path.basename(filepath)
                    mime_type, _ = guess_type(filename)
                    if not mime_type:
                        mime_type = 'application/octet-stream'
                    
                    maintype, subtype = mime_type.split('/', 1)
                    
                    with open(filepath, 'rb') as fp:
                        if maintype == 'audio':
                            part = MIMEAudio(fp.read(), _subtype=subtype)
                        else:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(fp.read())
                            encoders.encode_base64(part)
                        
                        part.add_header('Content-Disposition', 'attachment', filename=filename)
                        msg.attach(part)
                    print(f"Attached file: {filename}")
                except Exception as e:
                    print(f"Error attaching {filepath}: {e}")
            
            try:
                with smtplib.SMTP(config['email']['smtp_server'], config['email']['smtp_port']) as server:
                    server.starttls()
                    server.login(config['email']['sender_email'], config['email']['sender_password'])
                    server.send_message(msg)
                sent_count += 1
                print(f"Sent to {kid_email}")
            except Exception as e:
                error_msg = f"Failed to send to {kid_email}: {e}"
                print(error_msg)
                send_errors.append(error_msg)
        
        # CC parents - create fresh message for each
        for parent_email in parent_emails:
            body_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
                <h1 style="color: #4A90D9;">📖 A Story Just For You!</h1>
                <p>{sender_name} just created a journal entry!</p>
                <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; white-space: pre-wrap;">{story}</div>
                {thumbnails_html}
                {links_html}
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Made with ❤️ by Family Journal
                </p>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('mixed')
            msg['Subject'] = f"[CC] 📖 A Story from {sender_name}!"
            msg['From'] = f"{sender_name} <{config['email']['sender_email']}>"
            msg['To'] = parent_email
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            
            # Attach images if under limit
            if attach_images:
                for filepath in image_attachments:
                    try:
                        filename = os.path.basename(filepath)
                        mime_type, _ = guess_type(filename)
                        if not mime_type:
                            mime_type = 'application/octet-stream'
                        
                        with open(filepath, 'rb') as fp:
                            part = MIMEImage(fp.read(), _subtype=mime_type.split('/')[-1])
                            part.add_header('Content-Disposition', 'attachment', filename=filename)
                            msg.attach(part)
                    except Exception as e:
                        print(f"Error attaching image {filepath}: {e}")
            
            # Attach other local files
            for filepath in other_attachments:
                try:
                    filename = os.path.basename(filepath)
                    mime_type, _ = guess_type(filename)
                    if not mime_type:
                        mime_type = 'application/octet-stream'
                    
                    maintype, subtype = mime_type.split('/', 1)
                    
                    with open(filepath, 'rb') as fp:
                        if maintype == 'audio':
                            part = MIMEAudio(fp.read(), _subtype=subtype)
                        else:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(fp.read())
                            encoders.encode_base64(part)
                        
                        part.add_header('Content-Disposition', 'attachment', filename=filename)
                        msg.attach(part)
                except Exception as e:
                    print(f"Error attaching {filepath}: {e}")
            
            try:
                with smtplib.SMTP(config['email']['smtp_server'], config['email']['smtp_port']) as server:
                    server.starttls()
                    server.login(config['email']['sender_email'], config['email']['sender_password'])
                    server.send_message(msg)
                print(f"CC to {parent_email}")
            except Exception as e:
                print(f"Failed to CC to {parent_email}: {e}")
        
        # Return success even if some failed (as long as at least one sent)
        if send_errors:
            return jsonify({
                'success': True,
                'message': f'Story sent to {sent_count} kid(s)! ({", ".join(send_errors)})'
            })
        
        return jsonify({
            'success': True,
            'message': f'Story sent to {sent_count} kid(s)!'
        })
        
    except Exception as e:
        print(f"Submit error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
