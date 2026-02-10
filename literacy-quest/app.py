#!/usr/bin/env python3
"""
Literacy Quest - An RPG Reading Adventure for Kids!
Battle monsters by answering reading questions!
"""

import os
import json
import random
import yaml
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# Load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()
app = Flask(__name__)
app.secret_key = 'literacy-quest-secret-key'


def get_quest_data():
    """Get quest state from session."""
    if 'quest_data' not in session:
        session['quest_data'] = {
            'character': None,
            'hp': 10,
            'max_hp': 10,
            'xp': 0,
            'level': 1,
            'gold': 0,
            'current_monster': None,
            'monsters_defeated': 0,
            'questions_answered': 0,
            'correct_answers': 0,
            'streak': 0,
            'best_streak': 0,
            'inventory': [],
            'unlocked_worlds': ['forest'],
            'current_world': 'forest',
            'bosses_defeated': [],
            'achievements': [],  # List of achievement IDs earned
            'first_monster_defeated': False,
            'total_damage_dealt': 0
        }
    return session['quest_data']


def save_quest_data(data):
    """Save quest state to session."""
    session['quest_data'] = data
    session.modified = True


def get_characters():
    """Get all character classes."""
    return config.get('characters', [])


def get_monsters():
    """Get all monsters."""
    return config.get('monsters', [])

def get_achievements():
    """Get all achievements."""
    return config.get('achievements', [])

def get_encouragements(category='correct'):
    """Get random encouragement message."""
    encouragements = config.get('encouragements', {}).get(category, ["🌟 Great job!"])
    return random.choice(encouragements)

def check_achievements(quest_data):
    """Check for newly earned achievements."""
    new_achievements = []
    achievements = get_achievements()
    earned = quest_data.get('achievements', [])
    
    for ach in achievements:
        if ach['id'] in earned:
            continue
            
        # Check conditions
        earned_it = False
        
        if ach['id'] == 'first_monster' and quest_data.get('monsters_defeated', 0) >= 1:
            earned_it = True
        elif ach['id'] == 'ten_correct' and quest_data.get('correct_answers', 0) >= 10:
            earned_it = True
        elif ach['id'] == 'first_level_up' and quest_data.get('level', 1) >= 2:
            earned_it = True
        elif ach['id'] == 'streak_five' and quest_data.get('best_streak', 0) >= 5:
            earned_it = True
        elif ach['id'] == 'streak_ten' and quest_data.get('best_streak', 0) >= 10:
            earned_it = True
        elif ach['id'] == 'five_monsters' and quest_data.get('monsters_defeated', 0) >= 5:
            earned_it = True
        elif ach['id'] == 'twenty_correct' and quest_data.get('correct_answers', 0) >= 20:
            earned_it = True
        elif ach['id'] == 'three_streak' and quest_data.get('best_streak', 0) >= 3:
            earned_it = True
            
        if earned_it:
            new_achievements.append(ach)
            earned.append(ach['id'])
    
    return new_achievements


def get_questions_for_level(level):
    """Get reading questions for a level."""
    level_key = f"level_{level}"
    return config.get('questions', {}).get(level_key, [])


def get_random_question(level):
    """Get a random question for the given level."""
    questions = get_questions_for_level(level)
    if questions:
        return random.choice(questions)
    return None


def get_all_questions():
    """Get all questions from all levels."""
    all_q = []
    for i in range(1, 4):
        all_q.extend(get_questions_for_level(i))
    return all_q


def spawn_monster():
    """Spawn a new monster for the player to battle."""
    monsters = get_monsters()
    quest_data = get_quest_data()
    monsters_defeated = quest_data.get('monsters_defeated', 0)
    
    # Check for mini-boss every 5 monsters!
    is_boss = False
    if monsters_defeated > 0 and monsters_defeated % 5 == 0:
        is_boss = True
    
    # Filter monsters (only question-based monsters for now, or use simple damage questions)
    # For new emoji monsters, we use simple questions
    all_monsters = [m for m in monsters if m.get('id') not in ['word-eater', 'grammar-goblin']]
    
    if all_monsters:
        monster = random.choice(all_monsters)
        
        # Generate a simple damage question
        level = quest_data.get('level', 1)
        if is_boss:
            # Boss question
            question = random.choice([
                {"question": "What letter comes after A?", "options": ["B", "C", "D", "E"], "answer": "B"},
                {"question": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "answer": "4"},
                {"question": "Which is a color?", "options": ["Apple", "Blue", "Jump", "Run"], "answer": "Blue"},
            ])
        else:
            question = get_random_question(level)
            if not question:
                question = {"question": "What letter starts with S?", "options": ["Sun", "Cat", "Dog", "Pig"], "answer": "Sun"}
        
        # Bosses have more HP and special emoji
        hp = monster.get('hp', 10)
        if is_boss:
            hp = hp * 2  # Double HP for bosses
            emoji = monster.get('boss_emoji', monster.get('emoji'))
        else:
            emoji = monster.get('emoji')
        
        return {
            'id': monster['id'],
            'name': monster['name'],
            'emoji': emoji,
            'description': monster['description'],
            'hp': hp,
            'max_hp': hp,
            'question': question,
            'is_boss': is_boss,
            'is_mini_boss': monster.get('is_mini_boss', False)
        }
    else:
        # Fallback to original monsters
        monster = random.choice([m for m in monsters if m.get('id') in ['word-eater', 'grammar-goblin']])
        question = get_random_question(quest_data.get('level', 1))
        
        return {
            'id': monster['id'],
            'name': monster['name'],
            'emoji': monster['emoji'],
            'description': monster['description'],
            'hp': monster['hp'],
            'max_hp': monster['hp'],
            'question': question
        }


def check_level_up(xp):
    """Check if player levels up."""
    thresholds = [0, 50, 150, 350, 700, 1200]
    for i, threshold in enumerate(thresholds):
        if xp < threshold:
            return i + 1
    return len(thresholds)


@app.route('/')
def index():
    """Home page - Adventure map."""
    quest_data = get_quest_data()
    characters = get_characters()
    
    # Calculate stats
    xp_needed = [0, 50, 150, 350, 700, 1200]
    current_level = check_level_up(quest_data.get('xp', 0))
    next_threshold = xp_needed[current_level] if current_level < len(xp_needed) else None
    xp_progress = quest_data.get('xp', 0)
    xp_for_current = xp_needed[current_level - 1] if current_level > 1 else 0
    xp_percent = ((xp_progress - xp_for_current) / (next_threshold - xp_for_current) * 100) if next_threshold else 100
    
    return render_template(
        'index.html',
        site_name=config['site']['name'],
        kid_name=config['kid']['name'],
        quest_data=quest_data,
        characters=characters,
        current_level=current_level,
        xp_progress=xp_progress,
        next_threshold=next_threshold,
        xp_percent=min(xp_percent, 100)
    )


@app.route('/select-character/<char_id>')
def select_character(char_id):
    """Select your character."""
    characters = {c['id']: c for c in get_characters()}
    if char_id in characters:
        quest_data = get_quest_data()
        quest_data['character'] = characters[char_id]
        quest_data['hp'] = 10
        quest_data['max_hp'] = 10
        save_quest_data(quest_data)
    return redirect(url_for('index'))


@app.route('/battle')
def battle():
    """Battle screen - fight a monster!"""
    quest_data = get_quest_data()
    
    if not quest_data.get('character'):
        return redirect(url_for('index'))
    
    # Always spawn a new monster/question on page load
    monster = spawn_monster()
    quest_data['current_monster'] = monster
    save_quest_data(quest_data)
    
    current_level = check_level_up(quest_data.get('xp', 0))
    
    return render_template(
        'battle.html',
        site_name=config['site']['name'],
        kid_name=config['kid']['name'],
        quest_data=quest_data,
        monster=monster,
        current_level=current_level
    )


@app.route('/api/answer', methods=['POST'])
def answer_question():
    """Submit an answer to the current question."""
    data = request.json
    answer = data.get('answer', '').strip()
    
    quest_data = get_quest_data()
    monster = quest_data.get('current_monster', {})
    
    if not monster or not monster.get('question'):
        return jsonify({'error': 'No active battle'})
    
    question = monster.get('question', {})
    correct = answer.upper() == question.get('answer', '').upper()
    
    quest_data['questions_answered'] = quest_data.get('questions_answered', 0) + 1
    
    # Response data
    response_data = {
        'correct': correct,
        'streak': quest_data.get('streak', 0)
    }
    
    if correct:
        quest_data['correct_answers'] = quest_data.get('correct_answers', 0) + 1
        quest_data['streak'] = quest_data.get('streak', 0) + 1
        
        # Update best streak
        if quest_data['streak'] > quest_data.get('best_streak', 0):
            quest_data['best_streak'] = quest_data['streak']
        
        # Calculate XP gain
        xp_gain = 5
        streak = quest_data.get('streak', 0)
        damage = 3  # Base damage
        
        # Streak bonuses
        if streak >= 3:
            xp_gain += 3  # +3 bonus XP
            damage = 4    # +1 damage
        if streak >= 5:
            xp_gain += 5  # +5 bonus XP
            damage = 6    # DOUBLE damage for critical hit!
        
        quest_data['xp'] = quest_data.get('xp', 0) + xp_gain
        quest_data['total_damage_dealt'] = quest_data.get('total_damage_dealt', 0) + damage
        
        # Damage the monster
        monster_hp_before = monster.get('hp', 0)
        monster['hp'] = max(0, monster.get('hp', 1) - damage)
        
        response_data['damage'] = damage
        response_data['xp_gain'] = xp_gain
        response_data['monster_hp'] = monster.get('hp')
        response_data['streak'] = streak
        
        # Encouragement messages
        if streak >= 5:
            response_data['encouragement'] = get_encouragements('critical')
            response_data['critical'] = True
            response_data['message'] = f"{response_data['encouragement']} CRITICAL HIT! {damage} damage!"
        elif streak >= 3:
            response_data['encouragement'] = get_encouragements('streak')
            response_data['message'] = f"{response_data['encouragement']} {damage} damage! +{xp_gain} XP!"
        else:
            response_data['encouragement'] = get_encouragements('correct')
            response_data['message'] = f"{response_data['encouragement']} {damage} damage! +{xp_gain} XP!"
        
        # Check if monster defeated
        if monster.get('hp', 0) <= 0:
            quest_data['monsters_defeated'] = quest_data.get('monsters_defeated', 0) + 1
            
            # First monster achievement
            if not quest_data.get('first_monster_defeated'):
                quest_data['first_monster_defeated'] = True
            
            # Gold reward (more for bosses)
            is_boss = monster.get('is_boss', False)
            gold_reward = random.randint(5, 10) if is_boss else random.randint(3, 8)
            quest_data['gold'] = quest_data.get('gold', 0) + gold_reward
            
            quest_data['current_monster'] = None
            quest_data['streak'] = 0
            
            # Check for level up
            old_level = quest_data.get('level', 1)
            new_level = check_level_up(quest_data.get('xp', 0))
            leveled_up = new_level > old_level
            
            if leveled_up:
                quest_data['level'] = new_level
                quest_data['hp'] = min(quest_data['hp'] + 5, quest_data.get('max_hp', 10) + 5)  # Heal on level up
            
            # Check achievements
            new_achievements = check_achievements(quest_data)
            
            response_data['monster_defeated'] = True
            response_data['gold_found'] = gold_reward
            response_data['leveled_up'] = leveled_up
            response_data['new_level'] = new_level if leveled_up else None
            response_data['is_boss'] = is_boss
            response_data['new_achievements'] = [{'name': a['name'], 'icon': a['icon'], 'description': a['description']} for a in new_achievements]
            response_data['celebration'] = get_encouragements('defeated')
            
            save_quest_data(quest_data)
            
            return jsonify(response_data)
        
        save_quest_data(quest_data)
        return jsonify(response_data)
    else:
        quest_data['streak'] = 0
        quest_data['hp'] = quest_data.get('hp', 10) - 1
        
        response_data['streak'] = 0
        response_data['message'] = "💥 Oops! The monster attacks! -1 HP"
        response_data['encouragement'] = "💪 Keep trying! You can do it!"
        
        # Check if player lost
        if quest_data.get('hp', 0) <= 0:
            quest_data['hp'] = 0
            quest_data['current_monster'] = None
            quest_data['streak'] = 0
            save_quest_data(quest_data)
            
            return jsonify({
                'correct': False,
                'player_hp': 0,
                'defeated': True,
                'message': "😢 You were defeated! Try again!",
                'encouragement': "🌟 Great effort! Try again!"
            })
        
        save_quest_data(quest_data)
        return jsonify(response_data)


@app.route('/api/retreat', methods=['POST'])
def retreat():
    """Retreat from battle."""
    quest_data = get_quest_data()
    quest_data['current_monster'] = None
    quest_data['streak'] = 0
    save_quest_data(quest_data)
    return jsonify({'success': True})


@app.route('/api/use-special', methods=['POST'])
def use_special():
    """Use character special ability."""
    quest_data = get_quest_data()
    char = quest_data.get('character', {})
    
    if not char:
        return jsonify({'error': 'No character selected'})
    
    # For now, special heals or shields
    heal_amount = 3
    quest_data['hp'] = min(quest_data['hp'] + heal_amount, quest_data.get('max_hp', 10))
    save_quest_data(quest_data)
    
    return jsonify({
        'success': True,
        'new_hp': quest_data['hp'],
        'message': f"✨ {char.get('special_desc', 'Special used!')} +{heal_amount} HP!"
    })


@app.route('/api/reset', methods=['POST'])
def reset_quest():
    """Reset quest progress."""
    session.pop('quest_data', None)
    return jsonify({'success': True})


@app.route('/shop')
def shop():
    """Item shop."""
    quest_data = get_quest_data()
    
    items = [
        {'id': 'potion', 'name': 'Reading Potion', 'emoji': '🧪', 'cost': 10, 'desc': '+3 HP'},
        {'id': 'shield', 'name': 'Word Shield', 'emoji': '🛡️', 'cost': 15, 'desc': 'Block wrong answer'},
        {'id': 'scroll', 'name': 'Hint Scroll', 'emoji': '📜', 'cost': 20, 'desc': 'Remove 2 wrong options'},
    ]
    
    return render_template(
        'shop.html',
        site_name=config['site']['name'],
        kid_name=config['kid']['name'],
        quest_data=quest_data,
        items=items,
        gold=quest_data.get('gold', 0)
    )


@app.route('/api/buy/<item_id>', methods=['POST'])
def buy_item(item_id):
    """Buy an item from the shop."""
    quest_data = get_quest_data()
    gold = quest_data.get('gold', 0)
    
    items = {
        'potion': {'cost': 10, 'emoji': '🧪'},
        'shield': {'cost': 15, 'emoji': '🛡️'},
        'scroll': {'cost': 20, 'emoji': '📜'},
    }
    
    if item_id not in items:
        return jsonify({'error': 'Item not found'})
    
    cost = items[item_id]['cost']
    if gold < cost:
        return jsonify({'error': 'Not enough gold!'})
    
    quest_data['gold'] = gold - cost
    quest_data['inventory'] = quest_data.get('inventory', []) + [item_id]
    save_quest_data(quest_data)
    
    return jsonify({
        'success': True,
        'new_gold': quest_data['gold'],
        'item': items[item_id]['emoji'],
        'message': f"Bought {items[item_id]['emoji']}!"
    })


@app.route('/inventory')
def inventory():
    """View inventory."""
    quest_data = get_quest_data()
    
    items = {
        'potion': {'name': 'Reading Potion', 'emoji': '🧪', 'desc': '+3 HP', 'uses': 0},
        'shield': {'name': 'Word Shield', 'emoji': '🛡️', 'desc': 'Block 1 wrong answer', 'uses': 0},
        'scroll': {'name': 'Hint Scroll', 'emoji': '📜', 'desc': 'Remove 2 wrong options', 'uses': 0},
    }
    
    inventory = quest_data.get('inventory', [])
    inventory_counts = {item_id: inventory.count(item_id) for item_id in set(inventory)}
    
    return render_template(
        'inventory.html',
        site_name=config['site']['name'],
        kid_name=config['kid']['name'],
        quest_data=quest_data,
        inventory_counts=inventory_counts,
        items=items
    )


@app.route('/stats')
def stats():
    """Player statistics."""
    quest_data = get_quest_data()
    
    xp_needed = [0, 50, 150, 350, 700, 1200]
    current_level = check_level_up(quest_data.get('xp', 0))
    
    return render_template(
        'stats.html',
        site_name=config['site']['name'],
        kid_name=config['kid']['name'],
        quest_data=quest_data,
        current_level=current_level,
        xp_needed=xp_needed
    )


@app.route('/health')
def health():
    """Health check."""
    return jsonify({'status': 'ok', 'app': 'Literacy Quest'})


if __name__ == '__main__':
    app.run(
        host=config['app']['host'],
        port=config['app']['port'],
        debug=config['app']['debug']
    )
