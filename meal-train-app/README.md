# Reverse Meal Train - Bat Signal App

A Flask web application for coordinating meal deliveries using a "Bat Signal" approach.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export GMAIL_APP_PASSWORD="your-gmail-app-password"
   export FLASK_SECRET_KEY="your-secret-key"
   ```

3. **Initialize the database:**
   ```bash
   python3 app.py
   ```

4. **Run the app:**
   ```bash
   python3 app.py
   ```

   The app will be available at `http://localhost:5000`

## Configuration

Edit `config.yaml` to customize:
- Database path
- SMTP email settings (Gmail)
- App host/port
- Site name and family name

## Admin Login

- **URL:** `/login`
- **Username:** `kelly` or `landon`
- **Default Password:** `meal123` (change this in production!)

## Email Setup (Gmail)

1. Go to Google Account settings → Security
2. Enable 2-Step Verification
3. Go to App Passwords (https://myaccount.google.com/apppasswords)
4. Create a new app password for "Mail"
5. Use that password in the `GMAIL_APP_PASSWORD` environment variable

## How It Works

### 1. Subscribe
- Public page: enter name, email, phone (optional)
- Click "Subscribe to Bat Signal"

### 2. Admin Posts Meal Request
- Login as admin
- Click "Post Meal Request"
- Enter restaurant, amount, dietary notes
- Click "Send Bat Signal" → emails ALL subscribers

### 3. Claim Flow
- Subscriber receives Bat Signal email
- Email has link to claim page
- Choose payment method:
  - **Venmo:** @Landon-Atlas
  - **Own Payment:** Pay directly, Landon will cover the tab
- First to submit claims gets the meal!

### 4. After Claiming
- Claimer gets confirmation email with Venmo link
- Others who try to claim see "Already claimed" page
- Admin dashboard shows all claims

## Routes

| Route | Description |
|-------|-------------|
| `/` | Home page - shows current meal request |
| `/subscribe` | Sign up as subscriber |
| `/claim/<id>` | Claim a meal request (choose payment) |
| `/claim/<id>/confirm` | Confirm claim (POST) |
| `/login` | Admin login |
| `/admin` | Admin dashboard |
| `/admin/post-request` | Post new meal request |
| `/admin/subscribers` | View all subscribers |
| `/logout` | Admin logout |

## Database Schema

- **subscribers** - Name, email, phone, subscribed_at, active
- **admins** - Username, password_hash, name
- **meal_requests** - Restaurant, amount, notes, status, created_at, claimed_at
- **claims** - subscriber_id, meal_request_id, claim_method, claimed_at
- **email_logs** - Track sent emails

## Directory Structure

```
meal-train-app/
├── app.py           # Main Flask application
├── email_utils.py   # Email sending utilities
├── schema.sql       # Database schema
├── config.yaml      # Configuration file
├── requirements.txt # Python dependencies
└── templates/       # HTML templates
    ├── base.html
    ├── index.html
    ├── subscribe.html
    ├── claim.html
    ├── claim_success.html
    ├── already_claimed.html
    ├── login.html
    ├── admin.html
    ├── post_request.html
    ├── subscribers.html
    ├── 404.html
    └── 500.html
```

## Features

- 🚨 Bat Signal - emails all subscribers when dinner is needed
- 👥 Subscriber management
- 🔐 Admin authentication
- 🍽️ Restaurant and amount tracking
- 💰 Venmo and own payment options
- 📧 Confirmation emails
- 📱 Mobile-friendly dark theme
