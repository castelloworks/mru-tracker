from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import json
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'secret_key_anda'

# Lokasi fail
DATA_FILE = 'data/data_flat.xlsx'
LOG_FILE = 'data/log.json'

# User login - tambahkan admin juga
USERS = {
    'firdaus': 'firdaus123',
    'fitri': 'fitri123',
    'admin': 'admin123'
}

# Baca fail log
def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    return []

# Simpan ke fail log
def save_log(log):
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

# Home / Login page
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['username'] = username
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            error = 'Login gagal. Sila cuba lagi.'
    return render_template('login.html', error=error)

# Dashboard rider
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))

    mru_list = []
    message = ''

    if request.method == 'POST':
        mru_input = request.form['mru'].strip()
        df = pd.read_excel(DATA_FILE)
        log = load_log()

        # Check duplicate
        if any(entry['rider'] == session['username'] and entry['mru'] == mru_input for entry in log):
            message = f'❌ MRU {mru_input} telah dihantar sebelum ini oleh anda.'
        else:
            row = df[df['MR Unit'] == mru_input]
            if not row.empty:
                area = row.iloc[0]['STREET'] + ', ' + row.iloc[0]['CITY1']
                amount = int(row.iloc[0]['Sequence Number'])  # boleh tukar ikut column nilai sebenar

                log.append({
                    'rider': session['username'],
                    'mru': mru_input,
                    'area': area,
                    'amount': amount,
                    'timestamp': datetime.now().isoformat()
                })
                save_log(log)
                message = f'✅ MRU {mru_input} disimpan. Kawasan: {area}, Nilai: {amount}'
            else:
                message = f'❌ MRU {mru_input} tidak dijumpai.'

    # Senarai MRU yang telah dihantar oleh rider
    log = load_log()
    mru_list = [entry for entry in log if entry['rider'] == session['username']]

    return render_template('dashboard.html', username=session['username'], message=message, mru_list=mru_list)

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))

    # Load log daripada fail
    log = load_log()

    # Pastikan setiap item dalam log lengkap dengan field untuk paparan
    for item in log:
        item['rider'] = item.get('user', '')
        item['area'] = item.get('kawasan', '')
        item['amount'] = item.get('nilai', 0)

    # Tukar log kepada DataFrame untuk statistik
    df = pd.DataFrame(log)

    if df.empty:
        summary = []
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date

        # Kira jumlah MRU, jumlah nilai, dan bilangan hari bekerja
        summary = (
            df.groupby('rider')
            .agg(
                jumlah_mru=('mru', 'count'),
                jumlah_nilai=('amount', 'sum'),
                hari_bekerja=('date', 'nunique')
            )
            .reset_index()
            .to_dict(orient='records')
        )

    return render_template('admin_dashboard.html', log=log, summary=summary)


# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Run app
if __name__ == '__main__':
    app.run(debug=True)
