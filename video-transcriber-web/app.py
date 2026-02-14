#!/usr/bin/env python3
"""Video/Audio Transcriber Web App"""
import os
import subprocess
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/transcriber-uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ELEVENLABS_API_KEY = 'e1eddd1d04c1770684999c8d9a050d833a18cea0058a9e244f8d7485eab3e728'
ELEVENLABS_URL = 'https://api.elevenlabs.io/v1/speech-to-text'

def extract_audio(video_path, audio_path):
    """Extract audio from video to WAV format"""
    cmd = ['ffmpeg', '-y', '-i', video_path, '-ar', '16000', '-ac', '1', audio_path]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file
    filename = file.filename
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"video_{filename}")
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"audio_{filename}.wav")
    file.save(video_path)
    
    try:
        # Extract audio
        if not extract_audio(video_path, audio_path):
            # Try using original if it's already audio
            audio_path = video_path
        
        # Transcribe
        with open(audio_path, 'rb') as audio:
            files = {'file': ('audio.wav', audio, 'audio/wav')}
            data = {'model_id': 'scribe_v2', 'language_code': 'en'}
            headers = {'xi-api-key': ELEVENLABS_API_KEY}
            
            response = requests.post(ELEVENLABS_URL, files=files, data=data, headers=headers, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            transcript = result.get('text', '')
            
            # Cleanup
            try:
                os.remove(video_path)
                if audio_path != video_path and os.path.exists(audio_path):
                    os.remove(audio_path)
            except:
                pass
            
            return jsonify({'transcript': transcript})
        else:
            return jsonify({'error': 'Transcription failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup on error
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path) and audio_path != video_path:
                os.remove(audio_path)
        except:
            pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=False)
