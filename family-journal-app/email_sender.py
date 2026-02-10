import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email import encoders
import smtplib

class EmailSender:
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_story(self, recipients, subject, body, attachments=None):
        """
        Send a story with attached media to multiple recipients.
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            body: Email body (HTML or text)
            attachments: List of dicts with 'path', 'filename', 'mime_type'
        """
        if not recipients:
            raise ValueError("No recipients provided")
        
        # Create message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(recipients)
        
        # Create body part
        body_part = MIMEText(body, 'html', 'utf-8') if '<html>' in body else MIMEText(body, 'plain', 'utf-8')
        msg.attach(body_part)
        
        # Attach files
        if attachments:
            for att in attachments:
                try:
                    path = att['path']
                    filename = att.get('filename', os.path.basename(path))
                    mime_type = att.get('mime_type', 'application/octet-stream')
                    
                    if os.path.exists(path):
                        maintype, subtype = mime_type.split('/', 1)
                        
                        if maintype == 'image':
                            with open(path, 'rb') as fp:
                                img = MIMEImage(fp.read(), _subtype=subtype)
                                img.add_header('Content-Disposition', 'attachment', filename=filename)
                                msg.attach(img)
                        elif maintype == 'audio':
                            with open(path, 'rb') as fp:
                                audio = MIMEAudio(fp.read(), _subtype=subtype)
                                audio.add_header('Content-Disposition', 'attachment', filename=filename)
                                msg.attach(audio)
                        elif maintype == 'video':
                            with open(path, 'rb') as fp:
                                video = MIMEBase('video', subtype)
                                video.set_payload(fp.read())
                                encoders.encode_base64(video)
                                video.add_header('Content-Disposition', 'attachment', filename=filename)
                                msg.attach(video)
                        else:
                            with open(path, 'rb') as fp:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(fp.read())
                                encoders.encode_base64(part)
                                part.add_header('Content-Disposition', 'attachment', filename=filename)
                                msg.attach(part)
                except Exception as e:
                    print(f"Error attaching {path}: {e}")
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, msg.as_string())
            return True, "Email sent successfully"
        except Exception as e:
            return False, str(e)
    
    def send_to_child(self, child_email, child_name, story_body, media_files):
        """Convenience method to send a personalized story to a child."""
        subject = f"📖 A Special Story for You, {child_name}!"
        personalized_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
            <h1 style="color: #4A90D9;">Hey {child_name}! 🎉</h1>
            <p>Someone special created a story just for you!</p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 10px;">
                {story_body}
            </div>
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Made with ❤️ by your Family Journal App
            </p>
        </body>
        </html>
        """
        return self.send_story([child_email], subject, personalized_body, media_files)
