from flask import Flask, request, redirect, url_for, render_template, session
import pandas as pd
import json
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Fail data
DATA_FILE = 'data_flat.xlsx'
LOG_FILE = 'log.json'

# Fungsi muat log
def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r') as f:
        return json.load(f)

# Fungsi simpan log
def save_log(data):
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Fungsi baca data Excel
def load_excel_data():
    df = pd.read_excel(DATA_FILE)
    df['MRU'] = df['MRU'].astype(str)
    df.set_index('MRU', inplace=True)
    return df

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        rider = request.form['rider'].strip()
        if rider:
            session['rider'] = rider
            return redirect(url_for('submit'))
    return render_template('login.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if 'rider' not in session:
        return redirect(url_for('login'))

    msg = ''
    if request.method == 'POST':
        mru = request.form['mru'].strip()
        if not mru:
            msg = 'Sila masukkan nombor MRU.'
        else:
            df = load_excel_data()
            log = load_log()
            rider = session['rider']

            # Semak jika MRU wujud
            if mru not in df.index:
                msg = f'MRU {mru} tidak wujud dalam data.'
            else:
                # Semak jika sudah dihantar oleh rider ini
                existing = [entry for entry in log if entry['mru'] == mru and entry['rider'] == rider]
                if existing:
                    msg = f'MRU {mru} telah dihantar oleh {rider}.'
                else:
                    area = df.loc[mru]['Kawasan']
                    amount = int(df.loc[mru]['Jumlah'])
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    log.append({
                        'rider': rider,
                        'mru': mru,
                        'area': area,
                        'amount': amount,
                        'timestamp': timestamp
                    })
                    save_log(log)
                    msg = f'MRU {mru} berjaya direkodkan.'

    return render_template('submit.html', rider=session['rider'], message=msg)

@app.route('/admin')
def admin():
    log = load_log()

    # Summary per rider
    summary = {}
    for entry in log:
        rider = entry['rider']
        summary.setdefault(rider, {'jumlah_mru': 0, 'jumlah_nilai': 0})
        summary[rider]['jumlah_mru'] += 1
        summary[rider]['jumlah_nilai'] += entry['amount']

    summary_list = [{'rider': r, 'jumlah_mru': v['jumlah_mru'], 'jumlah_nilai': v['jumlah_nilai']} for r, v in summary.items()]

    return render_template('admin_dashboard.html', log=log, summary=summary_list)

@app.route('/logout')
def logout():
    session.pop('rider', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
