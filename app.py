from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
import os
import requests
import json

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# === SQLite Database ===
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "guard_system.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# === Models ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(50), nullable=False)

# === Seed Users ===
def seed_users():
    default_users = [
        {"username": "masteradmin", "password": "master123", "role": "masteradmin"},
        {"username": "admin", "password": "admin123", "role": "admin"},
        {"username": "guard", "password": "guard123", "role": "guard"},
    ]
    for user in default_users:
        if not User.query.filter_by(username=user["username"]).first():
            db.session.add(User(**user))
    db.session.commit()

with app.app_context():
    db.create_all()
    seed_users()

# === ROUTES ===

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        staff_id = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=staff_id, password=password).first()
        if user:
            session["role"] = user.role
            if user.role == "masteradmin":
                return redirect(url_for("masteradmin_dashboard"))
            elif user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role == "guard":
                return redirect(url_for("guard_dashboard"))
        return "Invalid credentials", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/masteradmin")
def masteradmin_dashboard():
    if session.get("role") != "masteradmin":
        return "403 Forbidden", 403
    hr_users = User.query.filter_by(role="hr").all()
    return render_template("masteradmin_dashboard.html", hr_users=hr_users)

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return "403 Forbidden", 403
    return render_template("admin_dashboard.html")

@app.route("/guard")
def guard_dashboard():
    if session.get("role") != "guard":
        return "403 Forbidden", 403
    return render_template("guard_dashboard.html")

@app.route("/hr")
def hr_dashboard():
    if session.get("role") != "hr":
        return "403 Forbidden", 403
    return render_template("hr_dashboard.html")

# === Singpass QR Login Route ===
@app.route("/singpass-login")
def singpass_login():
    auth_url = os.getenv("SINGPASS_LOGIN_URL")
    client_id = os.getenv("CLIENT_ID")
    redirect_uri = os.getenv("REDIRECT_URI")
    scope = os.getenv("SCOPE", "openid")
    return redirect(f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code")

# === Singpass Callback Handler ===
@app.route("/auth/callback")
def singpass_callback():
    code = request.args.get("code")
    if not code:
        return "Error: No code in callback.", 400

    # Exchange code for access token
    token_url = os.getenv("TOKEN_URL")
    client_id = os.getenv("CLIENT_ID")
    redirect_uri = os.getenv("REDIRECT_URI")

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code != 200:
        return f"Failed to retrieve token: {response.text}", 400

    token_data = response.json()
    id_token = token_data.get("id_token", "")

    # (Optional: Validate token using JWKS - skipped for simplicity here)
    # Set session
    session["role"] = "hr"  # or use real mapping from id_token
    return redirect(url_for("hr_dashboard"))

# === Run App ===
if __name__ == "__main__":
    app.run(debug=True)