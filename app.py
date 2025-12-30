from flask import Flask, render_template, request, jsonify
from flask import session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- CREATE TABLE ----------
def create_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # default admin (only first time)
    admin = conn.execute("SELECT * FROM admin").fetchone()
    if not admin:
        hashed_password = generate_password_hash("admin123")
        conn.execute(
        "INSERT INTO admin (username, password) VALUES (?, ?)",
        ("admin", hashed_password)
    )


    conn.commit()
    conn.close()


# ---------- HOME ----------
@app.route('/')
def home():
    return render_template('index.html')

# ---------- CONTACT API ----------
@app.route('/api/contact', methods=['POST'])
def contact_api():
    data = request.json

    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO contact (name, email, message) VALUES (?, ?, ?)",
        (name, email, message)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Message saved to database"
    })

# ---------- ADMIN API (VIEW DATA) ----------
@app.route('/api/messages')
def view_messages():
    conn = get_db_connection()
    messages = conn.execute("SELECT * FROM contact ORDER BY id DESC").fetchall()
    conn.close()

    result = []
    for msg in messages:
        result.append({
            "id": msg["id"],
            "name": msg["name"],
            "email": msg["email"],
            "message": msg["message"]
        })

    return jsonify(result)

# ---------- ADMIN PANEL ----------
@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        return redirect('/login')
    return render_template('admin.html')

# ---------- DELETE MESSAGE ----------
@app.route('/delete/<int:id>')
def delete_message(id):
    # 🔐 security: sirf admin hi delete kar sake
    if not session.get('admin'):
        return redirect('/login')

    conn = get_db_connection()
    conn.execute("DELETE FROM contact WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        admin = conn.execute(
            "SELECT * FROM admin WHERE username=?",
            (username,)
        ).fetchone()            
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session['admin'] = True
            return redirect('/admin')
        else:
            return "Invalid Login"

    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')

# ---------- RUN ----------
if __name__ == '__main__':
    create_table()
    app.run(host="0.0.0.0", port=10000)

