#!/usr/bin/env python3
"""
Crypto Tax Tracker - Auto-fetch transactions from blockchain explorers
"""

import json
import os
import sqlite3
import requests
import csv
from io import StringIO
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.config['DATABASE'] = 'crypto_tax.db'

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(app.config['DATABASE'])
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            network TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id INTEGER,
            tx_hash TEXT,
            type TEXT NOT NULL,
            token TEXT NOT NULL,
            amount REAL,
            price_per_token REAL,
            total_value REAL,
            fees REAL,
            platform TEXT,
            date TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wallet_id) REFERENCES wallets (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS nft_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id INTEGER,
            collection_name TEXT NOT NULL,
            token_id TEXT,
            purchase_price REAL,
            purchase_date TEXT,
            current_value REAL DEFAULT 0,
            is_rugged BOOLEAN DEFAULT FALSE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wallet_id) REFERENCES wallets (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    db = get_db()
    
    wallets = db.execute('SELECT * FROM wallets').fetchall()
    tx_count = db.execute('SELECT COUNT(*) as count FROM transactions').fetchone()
    nft_count = db.execute('SELECT COUNT(*) as count FROM nft_purchases WHERE is_rugged = 1').fetchone()
    
    total_sold = db.execute('SELECT COALESCE(SUM(total_value), 0) FROM transactions WHERE type = "sell"').fetchone()
    total_bought = db.execute('SELECT COALESCE(SUM(total_value), 0) FROM transactions WHERE type = "buy"').fetchone()
    nft_losses = db.execute('SELECT COALESCE(SUM(purchase_price), 0) FROM nft_purchases WHERE is_rugged = 1').fetchone()
    
    return render_template('index.html',
                          wallets=wallets,
                          tx_count=tx_count['count'],
                          nft_count=nft_count['count'],
                          total_sold=total_sold[0],
                          total_bought=total_bought[0],
                          nft_losses=nft_losses[0])

@app.route('/wallets', methods=['GET', 'POST'])
def wallets():
    db = get_db()
    
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        network = request.form.get('network', 'solana')
        
        wallet_id = db.execute('INSERT INTO wallets (name, address, network) VALUES (?, ?, ?)',
                             (name, address, network)).lastrowid
        db.commit()
        
        return redirect(url_for('wallets'))
    
    wallets = db.execute('SELECT * FROM wallets ORDER BY created_at DESC').fetchall()
    return render_template('wallets.html', wallets=wallets)

@app.route('/nfts', methods=['GET', 'POST'])
def nfts():
    db = get_db()
    
    if request.method == 'POST':
        collection = request.form.get('collection')
        token_id = request.form.get('token_id')
        price = float(request.form.get('price', 0))
        date = request.form.get('date')
        rugged = 'rugged' in request.form
        
        db.execute('''
            INSERT INTO nft_purchases (collection_name, token_id, purchase_price, purchase_date, is_rugged)
            VALUES (?, ?, ?, ?, ?)
        ''', (collection, token_id, price, date, rugged))
        db.commit()
        return redirect(url_for('nfts'))
    
    nfts = db.execute('SELECT * FROM nft_purchases ORDER BY purchase_date DESC').fetchall()
    total_losses = db.execute('SELECT COALESCE(SUM(purchase_price), 0) FROM nft_purchases WHERE is_rugged = 1').fetchone()
    
    return render_template('nfts.html', nfts=nfts, total_losses=total_losses[0])

@app.route('/report/<int:year>')
def tax_report(year):
    db = get_db()
    
    report = {
        'year': year,
        'transactions': [],
        'nft_losses': [],
        'total_gain_loss': 0
    }
    
    return render_template('report.html', report=report)

@app.route('/api/transactions')
def api_transactions():
    db = get_db()
    txs = db.execute('SELECT * FROM transactions ORDER BY date DESC LIMIT 100').fetchall()
    return jsonify([dict(tx) for tx in txs])

def parse_number(val):
    """Parse a number from various formats"""
    if val is None or val == '':
        return 0
    try:
        val = str(val).replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
        return float(val)
    except:
        return 0

def normalize_tx_type(tx_type, amount):
    """Normalize transaction type"""
    tx = str(tx_type).lower().strip()
    
    if 'open_long' in tx or ('long' in tx and 'open' in tx) or tx_type == 'buy':
        return 'buy'
    elif 'close_long' in tx or ('long' in tx and 'close' in tx) or tx == 'sell':
        return 'sell'
    elif 'open_short' in tx or ('short' in tx and 'open' in tx):
        return 'sell'
    elif 'close_short' in tx or ('short' in tx and 'close' in tx):
        return 'buy'
    elif 'deposit' in tx or 'withdraw' in tx or 'transfer' in tx:
        return 'transfer'
    elif 'fee' in tx or 'funding' in tx:
        return 'fee'
    else:
        return 'unknown'

def normalize_date(date_str):
    """Normalize date string to ISO format"""
    if not date_str:
        return datetime.now().isoformat()
    
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%Y %H:%M:%S', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt).isoformat()
        except:
            continue
    return date_str

@app.route('/upload')
def upload_page():
    """Upload CSV page"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    """Parse and import CSV transaction history"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    platform = request.form.get('platform', 'generic')
    
    try:
        content = file.read().decode('utf-8')
        reader = csv.DictReader(StringIO(content))
        
        db = get_db()
        imported = 0
        
        for row in reader:
            row_lower = {k.lower().strip(): v for k, v in row.items()}
            
            # Get common fields with fallback
            tx_type = row_lower.get('type') or row_lower.get('side') or row_lower.get('action') or 'unknown'
            token = row_lower.get('token') or row_lower.get('symbol') or row_lower.get('asset') or 'UNKNOWN'
            
            # Parse values
            amount = parse_number(row_lower.get('amount') or row_lower.get('size') or row_lower.get('quantity') or '0')
            total = parse_number(row_lower.get('total') or row_lower.get('value') or row_lower.get('usd_value') or row_lower.get('pnl') or '0')
            price = parse_number(row_lower.get('price') or row_lower.get('avg_price') or '0')
            fees = parse_number(row_lower.get('fees') or row_lower.get('fee') or row_lower.get('commission') or '0')
            
            date_str = row_lower.get('date') or row_lower.get('timestamp') or row_lower.get('time') or ''
            date = normalize_date(date_str)
            
            tx_type_norm = normalize_tx_type(tx_type, amount)
            
            db.execute('''
                INSERT INTO transactions (wallet_id, type, token, amount, price_per_token, total_value, fees, platform, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (0, tx_type_norm, token, amount, price, total, fees, platform, date))
            imported += 1
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': f'Imported {imported} transactions from {platform}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5005, debug=True)
