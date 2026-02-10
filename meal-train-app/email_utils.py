"""Email utilities for the Meal Train app."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import yaml
import os


def load_config():
    """Load configuration from config.yaml."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Replace environment variable placeholders
    if config['email']['password'].startswith('${'):
        env_var = config['email']['password'][2:-1]
        config['email']['password'] = os.environ.get(env_var, '')
    
    if config['app']['secret_key'].startswith('${'):
        env_var = config['app']['secret_key'][2:-1]
        config['app']['secret_key'] = os.environ.get(env_var, 'dev-secret-key')
    
    return config


def get_email_config():
    """Get email configuration."""
    config = load_config()
    return config['email']


def get_venmo_url():
    """Get Venmo URL from config."""
    config = load_config()
    venmo_config = config.get('venmo', {})
    return venmo_config.get('url', 'https://venmo.com')


def render_bat_signal_email(subscriber_name, restaurant, amount, family_name, claim_url):
    """Render the Meal Train email body."""
    venmo_url = get_venmo_url()
    
    body = f"""
🚂 MEAL TRAIN SIGNAL! 🚂

Hey {subscriber_name}!

The {family_name} could use some help with dinner!

🍽️  Restaurant: {restaurant}
💰 Amount Needed: {amount}
"""
    
    body += f"""
---

🏃‍♂️ BE THE FIRST TO CLAIM!
   Click below to cover the tab!

   👉 {claim_url}

   First one to claim gets to help!

---

💡 Your email will be removed from the list after you claim a meal.

Questions? Just reply to this email.

See you soon! 🍲
"""
    return body


def render_confirmation_email(subscriber_name, restaurant, amount, claim_method):
    """Render the confirmation email for the person who claimed."""
    venmo_url = get_venmo_url()
    
    body = f"""
🎉 YOU CLAIMED THE TAB! 🎉

Congratulations, {subscriber_name}!

You're covering the tab for {restaurant}!

💰 Amount: {amount}
"""
    
    if claim_method == 'venmo':
        body += f"""
---

💡 NEXT STEPS - SUBMIT PAYMENT:
   1. Venmo to cover the cost (or pay using your own method):
   
      👉 {venmo_url}

"""
    else:
        body += f"""
---

💡 NEXT STEPS - SUBMIT PAYMENT:
   1. I will organize my own payment method

"""
    
    body += """
Thank you for being part of our Meal Train! 🙌

Questions? Just reply to this email.
"""
    return body


def render_already_claimed_email(subscriber_name, restaurant):
    """Render email when someone tries to claim but it's already taken."""
    body = f"""
😢 Sorry, {subscriber_name}!

Someone else already claimed the tab for {restaurant}.

🏃‍♂️ You'll be first for the next Meal Train signal!

In the meantime, you can:
• Keep an eye out for the next meal request
• Reply to this email if you have questions

Thank you for being part of our community! 💙
"""
    return body


def send_email(to_email, subject, body, config=None):
    """Send an email via SMTP."""
    if config is None:
        config = get_email_config()
    
    msg = MIMEMultipart()
    msg['From'] = f"{config['from_name']} <{config['from_address']}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(config['host'], config['port'])
        server.starttls()
        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)


def send_bat_signal_email(subscriber_email, subscriber_name, restaurant, amount, 
                          family_name, claim_url, request_id):
    """Send a Meal Train signal email to a subscriber."""
    subject = f"🚨 MEAL TRAIN: {family_name} needs help with dinner from {restaurant}!"
    body = render_bat_signal_email(subscriber_name, restaurant, amount, 
                                   family_name, claim_url)
    return send_email(subscriber_email, subject, body)


def send_confirmation_email(subscriber_email, subscriber_name, restaurant, amount, claim_method):
    """Send confirmation email to the person who claimed."""
    subject = f"🎉 You claimed the tab for {restaurant}!"
    body = render_confirmation_email(subscriber_name, restaurant, amount, claim_method)
    return send_email(subscriber_email, subject, body)


def send_already_claimed_email(subscriber_email, subscriber_name, restaurant):
    """Send 'already claimed' email."""
    subject = f"😢 Sorry, {restaurant} tab is already claimed"
    body = render_already_claimed_email(subscriber_name, restaurant)
    return send_email(subscriber_email, subject, body)
