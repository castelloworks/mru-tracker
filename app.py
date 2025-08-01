from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ===================== CONFIG ===================== #
DATA_FILE = 'data_flat.xlsx'
LOG_FILE = 'log.json'

USERS = {
    'firdaus': 'firdaus123',
    'fitri': 'fitri123',
    'admin': 'admin123'
}

# ===================== FUNCTIONS ===================== #
def load_data():
    df = pd.read_excel(DATA_FILE)
    df.columns = ['MRU', 'Kawasan', 'Nilai']
    return df

def load_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            json.dump([], f)
    with open(LOG_FILE, 'r') as f:
        return json.load(f)

def save_log(log):
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def is_mru_exists(mru):
    df = load_data()
    return str(mru) in df['MRU'].astype(str).values

def get_mru_info(mru):
    df = load_data()
    match = df[df['MRU'].astype(str) == str(mru)]
    if not match.empty:
        return match.iloc[0].to_dict()
    return None

def has_user_submitted_mru(log, username, mru):
    return any(entry['username'] == username and entry['mru'] == mru for entry in log)

# ===================== ROUTES ===================== #
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in USERS and USERS[username] == password:
        session['username'] = username
        return redirect(url_for('dashboard'))
    flash('Login gagal. Sila semak nama dan kata laluan.', 'danger')
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    username = session['username']
    is_admin = username == 'admin'
    log = load_log()
    submitted = [entry for entry in log if entry['username'] == username]
    total_nilai = sum(entry['nilai'] for entry in submitted)

    if request.method == 'POST':
        mru_input = request.form['mru'].strip()
        if not is_mru_exists(mru_input):
            flash('MRU tidak dijumpai dalam data.', 'danger')
            return redirect(url_for('dashboard'))

        if has_user_submitted_mru(log, username, mru_input):
            flash('MRU ini telah dihantar sebelum ini oleh anda.', 'warning')
            return redirect(url_for('dashboard'))

        mru_info = get_mru_info(mru_input)
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'mru': mru_input,
            'kawasan': mru_info['Kawasan'],
            'nilai': int(mru_info['Nilai'])
        }
        log.append(log_entry)
        save_log(log)
        flash(f"MRU {mru_input} ({mru_info['Kawasan']}) berjaya direkodkan.", 'success')
        return redirect(url_for('dashboard'))

    if is_admin:
        # Statistik untuk admin
        stats = {}
        for entry in log:
            stats.setdefault(entry['username'], {'count': 0, 'total_nilai': 0})
            stats[entry['username']]['count'] += 1
            stats[entry['username']]['total_nilai'] += entry['nilai']
        return render_template('admin_dashboard.html', log=log[::-1], stats=stats)

    return render_template('dashboard.html', log=submitted[::-1], total_nilai=total_nilai)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Anda telah log keluar.', 'info')
    return redirect(url_for('index'))

# ===================== MAIN ===================== #
if __name__ == '__main__':
    app.run(debug=True)
