#!/usr/bin/env python3
"""
Baby Diana Meal Train - Dining Box Car Theme
Rebuilt from scratch with fun train metaphor
"""
import json
import os
import smtplib
import secrets
import yaml
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'meal-train-secret-rainbow')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Load config
with open('config.yaml') as f:
    config = yaml.safe_load(f)

DATABASE_FILE = config.get('database', 'database.json')
UPLOAD_FOLDER = config['app']['upload_folder']
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed extensions for receipt images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database functions
def load_db():
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as f:
            return json.load(f)
    return {'participants': [], 'meals': []}

def save_db(data):
    with open(DATABASE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_claim_code():
    return secrets.token_urlsafe(8)

def format_time_ago(dt):
    """Format datetime as 'X hours ago' or similar"""
    # Parse string if needed
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return "Just now"

# Routes
@app.route('/')
def index():
    db = load_db()
    
    # Get all participants
    all_participants = db['participants']
    
    return render_template('index.html',
                         participants=all_participants)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Sign up for meal train
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        if not name or not email:
            return render_template('signup.html', error="Please enter both name and email")
        
        db = load_db()
        
        # Check if already signed up - if so, just show welcome back
        for p in db['participants']:
            if p['email'] == email:
                return render_template('signup.html', 
                    message=f"Welcome back, {p['name']}! You're already on the meal train! 🚂")
        
        # Add new participant
        participant = {
            'id': secrets.token_urlsafe(16),
            'name': name,
            'email': email,
            'joined_at': datetime.now().isoformat()
        }
        db['participants'].append(participant)
        save_db(db)
        
        return render_template('signup_success.html', name=name, email=email)
    
    return render_template('signup.html')

# Claim a meal via email link - show payment options
@app.route('/claim/<meal_id>')
def claim_meal(meal_id):
    db = load_db()
    
    # Find meal
    meal = None
    for m in db['meals']:
        if m['id'] == meal_id:
            meal = m
            break
    
    if not meal:
        return render_template('claim_error.html', message="This meal request has expired or been deleted.")
    
    if meal.get('claimed'):
        return render_template('claim_error.html', message="This meal has already been claimed!")
    
    # Get participant info from email param
    participant_email = request.args.get('email')
    participant_name = None
    if participant_email:
        for p in db['participants']:
            if p['email'] == participant_email:
                participant_name = p['name']
                break
    
    return render_template('claim_form.html', meal=meal, participant_name=participant_name)

# Confirm claim with payment method
@app.route('/claim/<meal_id>/confirm', methods=['POST'])
def confirm_claim(meal_id):
    payment_method = request.form.get('method', 'other')
    
    db = load_db()
    
    # Find meal
    meal = None
    for m in db['meals']:
        if m['id'] == meal_id:
            meal = m
            break
    
    if not meal:
        return render_template('claim_error.html', message="This meal request has expired or been deleted.")
    
    if meal.get('claimed'):
        return render_template('claim_error.html', message="This meal has already been claimed!")
    
    # Get participant email from form
    participant_email = request.form.get('email', '')
    
    # Remove participant from list (so they can resubscribe later)
    if participant_email:
        db['participants'] = [p for p in db['participants'] if p['email'] != participant_email]
        save_db(db)
    
    # Mark meal as claimed
    meal['claimed'] = True
    meal['claimed_at'] = datetime.now().isoformat()
    meal['payment_method'] = payment_method
    meal['participant_email'] = participant_email
    save_db(db)
    
    # Show success with appropriate payment info
    return render_template('claim_success.html', meal=meal, payment_method=payment_method)

# Admin login
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@admin_required
def admin():
    db = load_db()
    
    # Get all meals with formatted times
    meals = []
    for m in db['meals']:
        created = datetime.fromisoformat(m['created_at'])
        m['time_ago'] = format_time_ago(created)
        m['formatted_date'] = created.strftime('%b %d, %Y at %I:%M %p')
        meals.append(m)
    
    # Sort: unclaimed first, then by date
    meals.sort(key=lambda x: (x.get('claimed', False), -datetime.fromisoformat(x['created_at']).timestamp()))
    
    participants = sorted(db['participants'], key=lambda x: x.get('joined_at', ''))
    
    # Calculate stats
    total_meals = len(db['meals'])
    claimed_meals = len([m for m in db['meals'] if m.get('claimed')])
    pending_meals = total_meals - claimed_meals
    
    # Get success message from query params
    success_message = request.args.get('success', '')
    
    return render_template('admin.html',
                         meals=meals,
                         participants=participants,
                         stats={'total': total_meals, 'claimed': claimed_meals, 'pending': pending_meals},
                         success_message=success_message)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == config['admin']['password']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        error = "Incorrect password"
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# Admin actions
@app.route('/admin/create-meal', methods=['POST'])
@admin_required
def create_meal():
    """Create a new meal request"""
    note = request.form.get('note', '').strip()
    meal_type = request.form.get('meal_type', '').strip()
    amount = request.form.get('amount', '').strip()
    
    # Handle receipt image upload
    receipt_filename = None
    if 'receipt' in request.files:
        file = request.files['receipt']
        if file and file.filename and allowed_file(file.filename):
            receipt_filename = f"{secrets.token_urlsafe(16)}_{file.filename}"
            file.save(os.path.join(UPLOAD_FOLDER, receipt_filename))
    
    db = load_db()
    
    meal = {
        'id': secrets.token_urlsafe(12),
        'note': note,
        'meal_type': meal_type,
        'amount': amount,
        'receipt_image': receipt_filename,
        'claimed': False,
        'created_at': datetime.now().isoformat(),
        'email_sent': False
    }
    
    db['meals'].insert(0, meal)
    save_db(db)
    
    # Send notifications to participants
    try:
        send_meal_request_notification(db['participants'], meal)
        meal['email_sent'] = True
        save_db(db)
    except Exception as e:
        print(f"Failed to send notifications: {e}")
    
    return redirect(url_for('admin', success='Meal request sent successfully!'))

@app.route('/admin/delete-meal/<meal_id>')
@admin_required
def delete_meal(meal_id):
    db = load_db()
    meal = None
    for m in db['meals']:
        if m['id'] == meal_id:
            meal = m
            break
    
    meal_name = meal.get('meal_type', 'Meal') if meal else 'Meal'
    db['meals'] = [m for m in db['meals'] if m['id'] != meal_id]
    save_db(db)
    return redirect(url_for('admin', success=f'{meal_name} has been deleted'))

@app.route('/admin/delete-participant/<participant_id>')
@admin_required
def delete_participant(participant_id):
    db = load_db()
    participant = None
    for p in db['participants']:
        if p['id'] == participant_id:
            participant = p
            break
    
    participant_name = participant.get('name', 'Participant') if participant else 'Participant'
    db['participants'] = [p for p in db['participants'] if p['id'] != participant_id]
    save_db(db)
    return redirect(url_for('admin', success=f'{participant_name} has been removed from the train'))

@app.route('/admin/resend-notification/<meal_id>')
@admin_required
def resend_notification(meal_id):
    db = load_db()
    
    meal = None
    for m in db['meals']:
        if m['id'] == meal_id:
            meal = m
            break
    
    if meal and not meal.get('claimed'):
        try:
            send_meal_request_notification(db['participants'], meal)
            meal['email_sent'] = True
            save_db(db)
            return jsonify({'success': True, 'message': 'Notifications resent!'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    return jsonify({'success': False, 'message': 'Meal not found or already claimed'})

# Email functions
def send_meal_request_notification(participants, meal):
    """Send email to all participants about a new meal request"""
    if not participants:
        return
    
    subject = "🚂 Atlas Family Meal Train - Claim your boxcar!"
    
    for participant in participants:
        try:
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = f"{config['email']['sender_name']} <{config['email']['sender_email']}>"
            msg['To'] = participant['email']
            
            claim_url = url_for('claim_meal', meal_id=meal['id'], email=participant['email'], _external=True)
            
            # Build meal details
            meal_details = ""
            if meal.get('meal_type'):
                meal_details += f"<p style='font-size: 24px; font-weight: bold; color: #667eea;'>{meal['meal_type']}</p>"
            if meal.get('amount'):
                meal_details += f"<p style='font-size: 28px; font-weight: bold; color: #48bb78;'>${meal['amount']}</p>"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #667eea;">🚂 Baby Diana Meal Train</h1>
                </div>
                <p>Hi {participant['name']}!</p>
                <div style="font-size: 18px; padding: 20px; background: #f0f4ff; border-radius: 10px; margin: 20px 0;">
                    <p><strong>The Atlas family just ordered a meal. Do you want to claim your boxcar and cover the tab?</strong></p>
                    {meal_details}
                </div>
                {f"<p><em>Note: {meal['note']}</em></p>" if meal.get('note') else ''}
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{claim_url}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 18px;">
                        🚃 Claim Your Boxcar!
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    First to claim gets to feed the family!<br>
                    Your dining box car will be removed from the train.<br>
                    <a href="{claim_url}">{claim_url}</a>
                </p>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">
                    Made with ❤️ by Baby Diana Meal Train
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Attach receipt image if available
            receipt_image = meal.get('receipt_image')
            if receipt_image:
                receipt_path = os.path.join(UPLOAD_FOLDER, receipt_image)
                if os.path.exists(receipt_path):
                    with open(receipt_path, 'rb') as f:
                        img_data = f.read()
                    image = MIMEImage(img_data)
                    image.add_header('Content-Disposition', 'attachment', filename=receipt_image)
                    image.add_header('Content-ID', '<receipt_image>')
                    msg.attach(image)
            
            with smtplib.SMTP(config['email']['smtp_server'], config['email']['smtp_port']) as server:
                server.starttls()
                server.login(config['email']['sender_email'], config['email']['sender_password'])
                server.send_message(msg)
            
            print(f"📧 Sent notification to {participant['email']}")
        except Exception as e:
            print(f"Failed to send to {participant['email']}: {e}")

def send_claim_confirmation(meal, participant):
    """Send confirmation when someone claims a meal"""
    msg = MIMEMultipart('mixed')
    msg['Subject'] = "✅ You claimed a dining box car!"
    msg['From'] = f"{config['email']['sender_name']} <{config['email']['sender_email']}>"
    msg['To'] = participant['email']
    
    venmo_url = config['venmo']['url']
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #48bb78;">🎉 You're on the train!</h1>
        </div>
        <p>Hi {participant['name']}!</p>
        <p style="font-size: 18px; padding: 20px; background: #f0fff4; border-radius: 10px;">
            ✅ You successfully claimed the meal!<br>
            Your dining box car has been added to the train! 🚂
        </p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{venmo_url}" style="display: inline-block; padding: 16px 32px; background: #008CFF; color: white; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 18px;">
                💳 Pay via Venmo
            </a>
        </p>
        <p style="color: #666; font-size: 14px; text-align: center;">
            Questions? Reply to this email!
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            Made with ❤️ by Baby Diana Meal Train
        </p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html', 'utf-8'))
    
    with smtplib.SMTP(config['email']['smtp_server'], config['email']['smtp_port']) as server:
        server.starttls()
        server.login(config['email']['sender_email'], config['email']['sender_password'])
        server.send_message(msg)
    
    print(f"📧 Sent claim confirmation to {participant['email']}")

# Import yaml at module level

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['app']['port'], debug=False)
