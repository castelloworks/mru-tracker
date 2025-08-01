from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

LOG_FILE = 'data/log.json'
DATA_FILE = 'data/data_flat.xlsx'

# Load MRU data from Excel
def load_data():
    df = pd.read_excel(DATA_FILE)
    mru_totals = df.groupby('MR Unit')['Device No.'].count().to_dict()
    return mru_totals

# Read log from JSON
def read_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r') as f:
        return json.load(f)

# Write log to JSON
def write_log(log):
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=4)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username == 'admin' and password == 'admin123') or (username == 'firdaus' and password == 'firdaus123') or (username == 'fitri' and password == 'fitri123'):
            session['username'] = username
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Nama atau kata laluan salah.')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    log = read_log()
    rider = session.get('username')

    # Elakkan crash jika log kosong
    mru_list = [entry for entry in log if entry.get('rider') == rider]

    return render_template('dashboard.html', username=rider, mru_list=mru_list)

@app.route('/submit', methods=['POST'])
def submit():
    if 'username' not in session:
        return redirect(url_for('login'))

    mru_number = request.form['mru_number']
    rider = session['username']
    log = read_log()
    mru_totals = load_data()

    # Elak duplicate oleh rider yang sama
    if any(entry.get('mru') == mru_number and entry.get('rider') == rider for entry in log):
        return redirect(url_for('dashboard'))

    jumlah = mru_totals.get(mru_number, 0)
    log.append({
        'mru': mru_number,
        'jumlah': jumlah,
        'rider': rider,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    write_log(log)
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))

    log = read_log()
    mru_totals = load_data()

    # Statistik setiap rider
    rider_stats = {}
    for entry in log:
        rider = entry.get('rider')
        jumlah = entry.get('jumlah', 0)
        if rider not in rider_stats:
            rider_stats[rider] = {'total_mru': 0, 'total_surat': 0}
        rider_stats[rider]['total_mru'] += 1
        rider_stats[rider]['total_surat'] += jumlah

    return render_template('admin_dashboard.html', log=log, rider_stats=rider_stats)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
