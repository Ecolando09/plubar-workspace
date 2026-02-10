-- Updated Database Schema for Reverse Meal Train (Bat Signal)

-- Subscribers table - people who signed up for the Bat Signal
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT 1
);

-- Admin users table
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meal requests table - when the family needs dinner
CREATE TABLE IF NOT EXISTS meal_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant TEXT NOT NULL,
    amount TEXT NOT NULL,
    notes TEXT,
    status TEXT DEFAULT 'pending',  -- pending, claimed, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    claimed_at TIMESTAMP
);

-- Claims table - who is bringing which meal
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_request_id INTEGER NOT NULL,
    subscriber_id INTEGER NOT NULL,
    claim_method TEXT NOT NULL,  -- 'venmo' or 'own_payment'
    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meal_request_id) REFERENCES meal_requests(id),
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(id),
    UNIQUE(meal_request_id)  -- Only one person can claim a request
);

-- Email log - track sent emails
CREATE TABLE IF NOT EXISTS email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_request_id INTEGER,
    email_type TEXT,  -- 'bat_signal', 'confirmation', 'already_claimed'
    sent_to TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subject TEXT,
    success BOOLEAN DEFAULT 1,
    error_message TEXT
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
CREATE INDEX IF NOT EXISTS idx_meal_requests_status ON meal_requests(status);
CREATE INDEX IF NOT EXISTS idx_claims_meal_request_id ON claims(meal_request_id);
