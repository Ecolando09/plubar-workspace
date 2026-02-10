from flask import Flask, render_template, request, jsonify, redirect, url_for
import yaml
import json
import os
from datetime import datetime
import uuid
import requests

app = Flask(__name__)

# Load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Story storage file
STORIES_FILE = config['storage']['stories_file']

def load_stories():
    if os.path.exists(STORIES_FILE):
        with open(STORIES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_stories(stories):
    with open(STORIES_FILE, 'w') as f:
        json.dump(stories, f, indent=2)

# Gemini API for story generation
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyBb-XPGzEOqKF70UFRFr2HG2oPTVCFva50')
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

def generate_story_with_ai(age, name, details, positive_value):
    """Generate a personalized story using Gemini AI"""
    
    age_prompts = {
        '3': "Use very simple words, short sentences (5-7 sentences), repetitive phrases. Focus on one main idea.",
        '4': "Gentle adventure, simple plot (7-9 sentences). Curious protagonist discovering something new.",
        '5': "Mild challenge with problem-solving (9-11 sentences). Character overcomes a small obstacle.",
        '6': "Teamwork and challenges (11-13 sentences). Multiple characters working together to solve a problem."
    }
    
    prompt = f"""Write a short bedtime story for a {age}-year-old named {name}.

Story idea from the child: {details}

Positive value to include: {positive_value}

Requirements:
- {age_prompts.get(str(age), age_prompts['4'])}
- The story should teach the positive value naturally through the narrative
- End with a gentle, satisfying conclusion
- Make it cozy and perfect for bedtime
- Write ONLY the story text, no titles or introductions
- Keep it warm and imaginative
- Write in English
"""
    
    try:
        response = requests.post(GEMINI_URL, json={
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }, timeout=10)
        
        data = response.json()
        if 'candidates' in data:
            story_text = data['candidates'][0]['content']['parts'][0]['text']
            return {
                'title': f"{name}'s Magical Story",
                'content': story_text.strip(),
                'age_group': age,
                'values': [positive_value],
                'style': f"Age-appropriate for {age}-year-olds"
            }
    except Exception as e:
        print(f"Gemini API error: {e}")
    
    # Fallback to simple template if API fails
    return generate_fallback_story(age, name, details, positive_value)

def generate_fallback_story(age, name, details, positive_value):
    """Simple fallback story when AI is unavailable"""
    story = f"""Once upon a time, in a magical land, there was a little one named {name}.

{details}

Along the way, {name} learned about {positive_value} - how it makes everyone happy and brings friends together.

{name} went home with a warm heart, feeling proud and sleepy.

The end.

🌟 Sweet dreams, {name}! 🌙"""
    
    return {
        'title': f"{name}'s Magical Story",
        'content': story,
        'age_group': age,
        'values': [positive_value],
        'style': "Cozy bedtime tale"
    }

@app.route('/')
def index():
    return render_template('index.html', config=config)

@app.route('/create', methods=['POST'])
def create():
    data = request.form or request.json
    
    name = data.get('name', 'Little One')
    details = data.get('details', 'A magical adventure')
    positive_value = data.get('positive_value', 'kindness')
    age = data.get('age', '4')
    voice = data.get('voice', 'amy')
    
    # Generate story using AI
    story = generate_story_with_ai(age, name, details, positive_value)
    story['voice'] = voice
    
    return render_template('story.html', story=story, config=config)

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    
    story_id = str(uuid.uuid4())[:8]
    saved_story = {
        'id': story_id,
        'title': data.get('title', 'Untitled Story'),
        'content': data.get('content', ''),
        'voice': data.get('voice', 'amy'),
        'age_group': data.get('age_group', '4'),
        'values': data.get('values', []),
        'created_at': datetime.now().isoformat()
    }
    
    stories = load_stories()
    stories.insert(0, saved_story)
    save_stories(stories)
    
    return jsonify({'success': True, 'story_id': story_id})

@app.route('/library')
def library():
    stories = load_stories()
    return render_template('library.html', stories=stories, config=config)

@app.route('/story/<story_id>')
def view_story(story_id):
    stories = load_stories()
    story = next((s for s in stories if s['id'] == story_id), None)
    if story:
        return render_template('story.html', story=story, config=config)
    return redirect(url_for('library'))

@app.route('/delete/<story_id>', methods=['POST'])
def delete_story(story_id):
    stories = load_stories()
    stories = [s for s in stories if s['id'] != story_id]
    save_stories(stories)
    return redirect(url_for('library'))

@app.route('/tts/<filename>')
def play_audio(filename):
    """Serve generated TTS audio files"""
    return app.send_static_file(os.path.join('tts', filename))

if __name__ == '__main__':
    # Ensure stories file exists
    if not os.path.exists(STORIES_FILE):
        save_stories([])
    
    app.run(host='0.0.0.0', port=5004, debug=True)
