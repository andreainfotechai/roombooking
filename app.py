from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # your MySQL password
    'database': 'hotel_management'
}


def get_db_connection():
    return mysql.connector.connect(**db_config)


# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# Add receipt route
@app.route('/add_receipt', methods=['GET', 'POST'])
def add_receipt():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        date = request.form['date']
        room_no = request.form['room_no']
        room_type = request.form['room_type']
        guest_name = request.form['guest_name']
        mobile_no = request.form['mobile_no']
        amount = request.form['amount']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO receipts (date, room_no, room_type, guest_name, mobile_no, amount) VALUES (%s, %s, %s, %s, %s, %s)",
            (date, room_no, room_type, guest_name, mobile_no, amount)
        )
        conn.commit()
        receipt_id = cursor.lastrowid
        cursor.close()
        conn.close()

        flash('Receipt added successfully!', 'success')
        return redirect(url_for('view_receipt', receipt_id=receipt_id))

    return render_template('add_receipt.html')


# View receipt route
@app.route('/view_receipt/<int:receipt_id>')
def view_receipt(receipt_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM receipts WHERE id = %s", (receipt_id,))
    receipt = cursor.fetchone()
    cursor.close()
    conn.close()

    if not receipt:
        flash('Receipt not found', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('view_receipt.html', receipt=receipt)


# View reports route
@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM receipts ORDER BY date DESC")
    receipts = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('reports.html', receipts=receipts)


# Delete receipt route
@app.route('/delete_receipt/<int:receipt_id>', methods=['POST'])
def delete_receipt(receipt_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM receipts WHERE id = %s", (receipt_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'success': True, 'message': 'Receipt deleted successfully'})


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)