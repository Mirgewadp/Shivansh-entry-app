from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'mirgewad_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# अपलोड फोल्डर तयार करणे
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            name TEXT,
            mobile TEXT,
            type_of_work TEXT,
            pending_amount REAL,
            credit_amount REAL,
            payment_mode TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def login_page():
    if session.get('loggedin'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    password = request.form.get('password')

    if user_id == '476137' and username == 'Shivanshm' and password == 'shivansh@2026':
        session['loggedin'] = True
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error="चूक! User ID, User Name किंवा Password तपासा.")

@app.route('/dashboard')
def dashboard():
    if not session.get('loggedin'):
        return redirect(url_for('login_page'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries ORDER BY id DESC")
    rows = cursor.fetchall()

    total_pending = sum(row[5] for row in rows if row[5])
    total_credit = sum(row[6] for row in rows if row[6])

    conn.close()
    
    profile_pic = session.get('profile_pic', 'https://via.placeholder.com/80')
    return render_template('index.html', entries=rows, total_pending=total_pending, total_credit=total_credit, profile_pic=profile_pic)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('loggedin'):
        return redirect(url_for('login_page'))

    name = request.form['name']
    mobile = request.form.get('mobile', '')
    type_of_work = request.form['type_of_work']
    pending_amount = float(request.form.get('pending_amount', 0))
    credit_amount = float(request.form.get('credit_amount', 0))
    payment_mode = request.form.get('payment_mode', '')
    date_today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO entries (date, name, mobile, type_of_work, pending_amount, credit_amount, payment_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date_today, name, mobile, type_of_work, pending_amount, credit_amount, payment_mode))
    conn.commit()
    conn.close()

    flash('Entry Added Successfully!', 'success')
    return redirect(url_for('dashboard'))

# फोटो सेव्ह करण्यासाठी नवीन मार्ग (Upload Route)
@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if not session.get('loggedin'):
        return redirect(url_for('login_page'))

    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file.filename != '':
            filename = 'profile_' + str(int(datetime.now().timestamp())) + '.' + file.filename.split('.')[-1]
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            session['profile_pic'] = url_for('static', filename='uploads/' + filename)

    return redirect(url_for('dashboard'))

@app.route('/download_excel')
def download_excel():
    if not session.get('loggedin'):
        return redirect(url_for('login_page'))
    
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query("SELECT * FROM entries", conn)
    conn.close()
    
    file_path = "entries_report.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    if not session.get('loggedin'):
        return redirect(url_for('login_page'))
    
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            df = pd.read_excel(file)
            conn = sqlite3.connect('database.db')
            for _, row in df.iterrows():
                conn.execute('''
                    INSERT INTO entries (date, name, mobile, type_of_work, pending_amount, credit_amount, payment_mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(row.get('date', datetime.now().strftime("%Y-%m-%d"))),
                    str(row.get('name', '')),
                    str(row.get('mobile', '')),
                    str(row.get('type_of_work', '')),
                    float(row.get('pending_amount', 0)),
                    float(row.get('credit_amount', 0)),
                    str(row.get('payment_mode', ''))
                ))
            conn.commit()
            conn.close()
            
            flash('Excel File Uploaded Successfully!', 'success')
            
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_entry(id):
    if not session.get('loggedin'):
        return redirect(url_for('login_page'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form.get('mobile', '')
        type_of_work = request.form['type_of_work']
        pending_amount = float(request.form.get('pending_amount', 0))
        credit_amount = float(request.form.get('credit_amount', 0))
        payment_mode = request.form.get('payment_mode', '')

        cursor.execute('''
            UPDATE entries 
            SET name=?, mobile=?, type_of_work=?, pending_amount=?, credit_amount=?, payment_mode=?
            WHERE id=?
        ''', (name, mobile, type_of_work, pending_amount, credit_amount, payment_mode, id))
        conn.commit()
        conn.close()
        
        flash('Entry Updated Successfully!', 'success')
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM entries WHERE id=?", (id,))
    entry = cursor.fetchone()
    conn.close()
    return render_template('edit.html', entry=entry)

@app.route('/update/<int:id>', methods=['POST'])
def update_entry(id):
    if not session.get('loggedin'):
        return redirect(url_for('login_page'))
        
    name = request.form.get('name')
    mobile = request.form.get('mobile')
    type_of_work = request.form.get('type_of_work')
    pending_amount = request.form.get('pending_amount')
    credit_amount = request.form.get('credit_amount')
    payment_mode = request.form.get('payment_mode')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE entries 
        SET name = ?, mobile = ?, type_of_work = ?, pending_amount = ?, credit_amount = ?, payment_mode = ?
        WHERE id = ?
    ''', (name, mobile, type_of_work, pending_amount, credit_amount, payment_mode, id))
    conn.commit()
    conn.close()
    
    flash('Entry Updated Successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:id>')
def delete_entry(id):
    if not session.get('loggedin'):
        return redirect(url_for('login_page'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE id=?", (id,))
    conn.commit()
    conn.close()
    
    flash('Entry Deleted Successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)
