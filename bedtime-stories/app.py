from flask import Flask, render_template, request, jsonify, redirect, url_for
import yaml
import json
import os
from datetime import datetime
import uuid
import requests
import hashlib
import random

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
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro:generateContent?key={GEMINI_API_KEY}"

# Curated imaginative settings based on age
MAGICAL_WORLDS = {
    '3': [
        "a candy kingdom where rivers flow with chocolate and lollipop trees sway in the breeze",
        "a cloud world where you can bounce on soft marshmallow clouds and meet friendly cloud animals",
        "an enchanted garden where flowers sing lullabies and butterflies leave sparkly dust",
        "a toy land where teddy bears have tea parties and toy trains take you anywhere you dream",
        "a rainbow meadow where every step creates musical notes and rainbows appear after giggles"
    ],
    '4': [
        "an underwater castle made of shimmering pearls with fish who paint pictures",
        "a treehouse village in a thousand-year-old oak tree where squirrels are master builders",
        "a wizard's garden where vegetables grow to enormous size and talk to you",
        "a rainbow bridge that leads to a new magical land each time you cross it",
        "a crystal cave that sparkles with a thousand colors and holds ancient secrets"
    ],
    '5': [
        "a dragon's mountain peak where fire-breathing dragons guard treasure but just want friends",
        "a floating island academy where young wizards learn to make magic with kindness",
        "an ancient temple hidden in the jungle with puzzles that only brave hearts can solve",
        "a time-travel garden where you can visit dinosaurs and future cities",
        "a pirate ship that sails through the clouds searching for treasure islands"
    ],
    '6': [
        "a forgotten kingdom beneath the sea where merpeople preserve ancient magic",
        "a secret society of young heroes who protect the world from shadow creatures",
        "an intergalactic academy where kids from different planets learn together",
        "a mystical dimension where dreams become real and nightmares can be befriended",
        "an ancient library that contains portals to any world you can imagine"
    ]
}

# Companion characters with creative names and descriptions
COMPANION_CHARACTERS = [
    ("Oliver", "a clever fox with orange fur and a聪明 face who knows every path in the forest"),
    ("Luna", "a magical owl with silver feathers who can see in the dark and whispers secrets"),
    ("Finn", "a adventurous sea turtle who swam all around the world and collects shiny stones"),
    ("Stella", "a sparkling unicorn with a rainbow mane who leaves glitter wherever she walks"),
    ("Atlas", "a strong mountain bear with thick brown fur who has a heart of gold"),
    ("Phoenix", "a gentle dragon who breathes bubbles instead of fire and loves to sing"),
    ("Willow", "a wise old tree sprite who lives in an ancient oak and knows ancient stories"),
    ("Jasper", "a mischievous ghost who loves to play pranks but has a kind heart"),
    ("Atlas", "a tiny dragon no bigger than a kitten who sneezes confetti"),
    ("Pippin", "a brave hedgehog who collected more acorns than anyone in the world"),
    ("Fern", "a young fairy with iridescent wings who can make flowers bloom instantly"),
    ("Bramble", "a grumpy but lovable troll who just wants someone to play with")
]

EXCITING_PROBLEMS = {
    '3': ["someone is lost and needs finding", "something magical is broken and needs fixing", "everyone forgot how to smile", "the stars fell from the sky", "a friend is scared and needs comfort"],
    '4': ["a dark cloud is blocking the sun", "someone stole the golden treasure", "the magic is draining away", "friends are fighting and need reconciling", "a curse turns everyone into stone"],
    '5': ["an ancient evil is awakening", "the portal home is closing", "someone was kidnapped by shadows", "a powerful artifact was broken", "the kingdom is under attack"],
    '6': ["a prophecy foretells doom", "time itself is unraveling", "an ancient evil has returned", "the chosen one has vanished", "the world is fading into nothingness"]
}

def generate_story_with_ai(age, name, details, positive_value, gender='any'):
    """Generate a genuinely captivating, imaginative story"""
    
    # Get pronouns based on gender preference
    pronouns = {
        'boy': {'subject': 'he', 'object': 'him', 'possessive': 'his'},
        'girl': {'subject': 'she', 'object': 'her', 'possessive': 'her'},
        'any': {'subject': 'they', 'object': 'them', 'possessive': 'their'}
    }.get(gender, {'subject': 'they', 'object': 'them', 'possessive': 'their'})
    
    # Pick random elements
    setting = random.choice(MAGICAL_WORLDS.get(str(age), MAGICAL_WORLDS['4']))
    companion = random.choice(COMPANION_CHARACTERS)
    problem = random.choice(EXCITING_PROBLEMS.get(str(age), EXCITING_PROBLEMS['4']))
    
    # Custom story seed if provided
    if details and details.strip() not in ['', 'A magical adventure', 'a magical adventure']:
        custom_elements = f"CHILD'S IDEA: {details}"
    else:
        custom_elements = f"A magical world where {setting}. {name} meets {companion[0]}, who is {companion[1]}. {problem.capitalize()}!"
    
    # Title templates
    title_templates = [
        f"{name}'s Incredible Adventure",
        f"{name} and the Magic of {positive_value.title()}",
        f"The {positive_value.title()} of {name}",
        f"{name}'s Unforgettable Journey",
        f"The Day {name} Became a Hero"
    ]
    title = random.choice(title_templates)
    
    # Build comprehensive story prompt
    word_count = {'3': '800-1200', '4': '1200-1800', '5': '1800-2500', '6': '2500-3500'}.get(str(age), '1500-2000')
    
    prompt = f"""{'='*60}
CHARACTER: {name}, Age: {age}, Pronouns: {pronouns['subject']}/{pronouns['object']}
POSITIVE VALUE: {positive_value.upper()}
COMPANION: {companion[0]} ({companion[1]})
{'='*60}

TASK: Write an ORIGINAL, CAPTIVATING bedtime story that will make this child EXCITED and IMAGINATIVE.

STORY ELEMENTS:
- Setting: {setting}
- Main Character: {name} ({pronouns['subject']} {pronouns['possessive']} adventures)
- Special Companion: {companion[0]} ({companion[1]})
- Central Problem: {problem}
- Core Lesson: {positive_value}

STORY STRUCTURE:

**OPENING (Make them gasp!):**
Start with SOMETHING UNEXPECTED - a sound, a sight, a feeling. Make the first sentence MEMORABLE.

**BUILDING WONDER (Sensory details!):**
Describe what {name} SEES: colors, shapes, magical elements
Describe what {name} HEARS: sounds, voices, music
Describe what {name} FEELS: emotions, textures, temperature
Use vivid, specific words - not generic ones!

**THE ADVENTURE (Exciting plot!):**
{name} and {companion[0]} encounter challenges and make discoveries together
Include at least 2-3 exciting moments or plot twists
Show the {positive_value} through ACTIONS, not just words
Let {name} be the HERO who saves the day!

**THE TRIUMPH (Satisfying ending!):**
{name} solves the problem using {positive_value}
Show the transformation - before and after
End with warmth, pride, and sweet dreams

REQUIREMENTS:
- {word_count} words - LONG and DETAILED
- Rich sensory descriptions (sight, sound, touch, feeling)
- Real character development for both {name} and {companion[0]}
- EXCITING plot with ups and downs
- The positive value shown through HEROIC ACTION
- Warm, cozy ending perfect for sleep
- NO lists, NO bullet points - pure prose
- NO moralizing or lecturing
- Make it SO GOOD the child begs for more stories

START WRITING IMMEDIATELY:

"""

    try:
        response = requests.post(GEMINI_URL, json={
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }, timeout=45)
        
        data = response.json()
        if 'candidates' in data:
            story_text = data['candidates'][0]['content']['parts'][0]['text']
            # Clean up any title/headers that might have been added
            if 'START WRITING IMMEDIATELY:' in story_text:
                story_text = story_text.split('START WRITING IMMEDIATELY:')[-1].strip()
            return {
                'title': title,
                'content': story_text.strip(),
                'age_group': age,
                'values': [positive_value],
                'style': f"Epic adventure for brave {age}-year-old heroes"
            }
    except Exception as e:
        print(f"Gemini API error: {e}")
    
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
    details = data.get('details', '')
    positive_value = data.get('positive_value', 'kindness')
    age = data.get('age', '4')
    voice = data.get('voice', 'adam')
    gender = data.get('gender', 'any')
    
    # Generate story using AI
    story = generate_story_with_ai(age, name, details, positive_value, gender)
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
        'voice': data.get('voice', 'adam'),
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

# ElevenLabs TTS Integration
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

def generate_tts(text, voice_id, api_key):
    """Generate TTS audio using ElevenLabs API"""
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    response = requests.post(
        f"{ELEVENLABS_API_URL}/{voice_id}",
        json=data,
        headers=headers
    )
    
    if response.status_code == 200:
        return response.content
    return None

def get_cache_path(text, voice_id):
    """Generate a cache filename for TTS audio"""
    text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
    return f"static/tts/{voice_id}_{text_hash}.mp3"

@app.route('/generate-tts', methods=['GET'])
def generate_tts_endpoint():
    """Generate TTS audio and return the file path"""
    text = request.args.get('text', '')
    voice_id = request.args.get('voice', 'adam')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Get voice ID from config
    voice_map = {
        'adam': config['tts']['elevenlabs']['voices']['adam']['id'],
        'bella': config['tts']['elevenlabs']['voices']['bella']['id'],
        'daniel': config['tts']['elevenlabs']['voices']['daniel']['id'],
        'antoni': config['tts']['elevenlabs']['voices']['antoni']['id'],
        'sarah': config['tts']['elevenlabs']['voices']['sarah']['id']
    }
    
    voice_config_id = voice_map.get(voice_id, voice_map['adam'])
    api_key = config['tts']['elevenlabs']['api_key']
    
    # Check cache
    cache_path = get_cache_path(text, voice_id)
    full_cache_path = os.path.join(app.root_path, cache_path)
    
    if os.path.exists(full_cache_path):
        return jsonify({
            'success': True,
            'audio_url': '/' + cache_path
        })
    
    # Generate new audio
    audio_content = generate_tts(text, voice_config_id, api_key)
    
    if audio_content:
        # Save to cache
        with open(full_cache_path, 'wb') as f:
            f.write(audio_content)
        
        return jsonify({
            'success': True,
            'audio_url': '/' + cache_path
        })
    else:
        return jsonify({'error': 'TTS generation failed'}), 500

@app.route('/tts/<filename>')
def play_audio(filename):
    """Serve generated TTS audio files"""
    return app.send_static_file(os.path.join('static', 'tts', filename))

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe uploaded audio using ElevenLabs Speech-to-Text"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        api_key = config['tts']['elevenlabs']['api_key']
        
        # Save temp file
        temp_path = '/tmp/upload_audio.wav'
        file.save(temp_path)
        
        # Transcribe using ElevenLabs
        response = requests.post(
            'https://api.elevenlabs.io/v1/speech-to-text',
            headers={'xi-api-key': api_key},
            files={'file': open(temp_path, 'rb')},
            data={'model_id': 'scribe_v2', 'language_code': 'en'}
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '')
            return jsonify({'success': True, 'transcription': text})
        else:
            return jsonify({'error': f'Transcription failed: {response.text}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure stories file exists
    if not os.path.exists(STORIES_FILE):
        save_stories([])
    
    app.run(host='0.0.0.0', port=5004, debug=True)
