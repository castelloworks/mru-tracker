from flask import Flask, render_template, request, redirect, url_for, session
import json
from datetime import datetime
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATA_FILE = 'data/log.json'
EXCEL_FILE = 'data/data_flat.xlsx'

# Pastikan data/log.json wujud
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# Baca Excel data MRU
def read_excel_data():
    df = pd.read_excel(EXCEL_FILE)
    mru_to_amount = {}
    for _, row in df.iterrows():
        mru = str(row['MRU']).strip()
        amount = int(row['JUMLAH']) if 'JUMLAH' in row and not pd.isna(row['JUMLAH']) else 0
        mru_to_amount[mru] = amount
    return mru_to_amount

# Baca log.json
def read_log():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Simpan log.json
def write_log(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        if username:
            session['username'] = username
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    log = read_log()
    mru_data = read_excel_data()
    rider = session.get('username')

    # Filter log ikut rider
    mru_list = [entry for entry in log if entry.get('rider') == rider]

    return render_template('dashboard.html', username=rider, mru_list=mru_list)

@app.route('/submit_mru', methods=['POST'])
def submit_mru():
    if 'username' not in session:
        return redirect(url_for('login'))

    mru_value = request.form['mru'].strip()
    log = read_log()

    # Cek sama ada MRU sudah wujud untuk rider ni
    if any(entry.get('rider') == session['username'] and entry.get('mru') == mru_value for entry in log):
        return "MRU telah dihantar oleh anda sebelum ini."

    mru_data = read_excel_data()
    amount_value = mru_data.get(mru_value, 0)

    new_entry = {
        "rider": session['username'],
        "mru": mru_value,
        "amount": amount_value,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    log.append(new_entry)
    write_log(log)
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin_dashboard():
    log = read_log()

    summary = {}
    for entry in log:
        rider = entry.get('rider')
        if not rider:
            continue
        if rider not in summary:
            summary[rider] = {'count': 0, 'total_amount': 0}
        summary[rider]['count'] += 1
        summary[rider]['total_amount'] += entry.get('amount', 0)

    return render_template('admin_dashboard.html', summary=summary, log=log)

if __name__ == '__main__':
    app.run(debug=True)
