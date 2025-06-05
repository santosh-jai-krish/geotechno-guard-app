from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "guard_system.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)

# Seed default users
def seed_users():
    default_users = [
        {"username": "masteradmin", "password": "master123", "role": "masteradmin"},
        {"username": "admin", "password": "admin123", "role": "admin"},
        {"username": "guard", "password": "guard123", "role": "guard"},
        {"username": "hr", "password": "hr123", "role": "hr"}
    ]
    for user in default_users:
        if not User.query.filter_by(username=user["username"]).first():
            db.session.add(User(**user))
    db.session.commit()

# Setup DB
with app.app_context():
    db.create_all()
    seed_users()

# Login route
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
            elif user.role == "hr":
                return redirect(url_for("hr_dashboard"))
        else:
            return "Invalid credentials", 401

    return render_template("login.html")

# Dashboards
@app.route("/masteradmin")
def masteradmin_dashboard():
    if session.get("role") != "masteradmin":
        return "403 Forbidden", 403
    return render_template("masteradmin_dashboard.html")

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

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=3000)