# Family Journal App

A simple Flask web app for capturing family memories and sending them to kids via email.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the app:
   - Edit `config.yaml` with:
     - Your email credentials (Gmail app password recommended)
     - Kid profiles (names and emails)
     - SMTP settings

3. Set your ElevenLabs API key:
```bash
export ELEVENLABS_API_KEY="your-api-key"
```

## Running the App

```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Features

- 📝 Write journal entries about your day
- 📷 Upload photos, videos, and voice recordings
- 👶 Manual kid selection via checkboxes
- 🎙️ Automatic voice transcription using ElevenLabs STT
- ✉️ Email compilation with attachments sent to all selected kids

## Kid Profiles

- Diana Atlas (buddhababediana@gmail.com)
- Jade Atlas (buddhababejade@gmail.com)
- Julian Atlas (buddhababejulian@gmail.com)

## Email Setup (Gmail)

1. Enable 2-factor authentication on your Google account
2. Go to Google Account > Security > App passwords
3. Create a new app password for "Mail"
4. Use this 16-character password in `config.yaml` as `sender_password`

## Project Structure

```
family-journal/
├── app.py              # Main Flask application
├── config.yaml         # Configuration file
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Main UI template
└── uploads/            # Temporary file storage
```
