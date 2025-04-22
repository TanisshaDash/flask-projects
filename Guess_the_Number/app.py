from flask import Flask, request, render_template, redirect, jsonify, make_response,session
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, unset_jwt_cookies
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('GUESS_DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT Settings
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

# --- Routes ---
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if not data.get("username") or not data.get("password"):
        return jsonify({"msg": "Username and password required"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"msg": "Username already exists"}), 400

    hashed_pw = generate_password_hash(data["password"])
    new_user = User(username=data["username"], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get("username")).first()
    if not user or not check_password_hash(user.password, data.get("password")):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.username)
    resp = jsonify({"msg": "Login successful"})
    resp.set_cookie("access_token_cookie", access_token, httponly=True)
    return resp

@app.route("/logout", methods=["POST"])
def logout():
    resp = jsonify({"msg": "Logged out"})
    unset_jwt_cookies(resp)
    return resp

@app.route("/start_game", methods=["GET"])
@jwt_required()
def start_game():
    target = random.randint(1, 50)
    attempts = 7  # Set attempts to 7 or whatever you want

    # Store the game state in the session
    session["target"] = target
    session["attempts"] = attempts

    return redirect("/play_game")

@app.route("/play_game", methods=["GET", "POST"])
@jwt_required()
def play_game():
    if request.method == "GET":
        # Get the game state (target and attempts) from the session
        target = session.get("target")
        attempts = session.get("attempts")

        if target is None or attempts is None:
            # If target or attempts are not found, redirect to the homepage
            return redirect("/")

        # Render the game page
        username = get_jwt_identity()
        return render_template("game.html", username=username, target=target, attempts=attempts, message="", game_over=False)

    # POST - handle form submission (guess logic)
    username = get_jwt_identity()
    guess = int(request.form["guess"])  # Ensure the guess is sent in the form data
    target = int(request.form["target"])
    attempts = int(request.form["attempts"]) - 1  # Decrease attempts by 1

    if guess == target:
        message = "🎉 Correct! You guessed it!"
        game_over = True
    elif attempts == 0:
        message = f"❌ No attempts left! The number was {target}."
        game_over = True
    else:
        message = "🔽 Too low!" if guess < target else "🔼 Too high!"
        game_over = False

    # Update the session with the new number of attempts
    session["target"] = target
    session["attempts"] = attempts

    return render_template("game.html", username=username, target=target, attempts=attempts, message=message, game_over=game_over)



@app.route("/submit_score", methods=["POST"])
@jwt_required()
def submit_score():
    username = get_jwt_identity()
    score = int(request.json.get("score", 0))

    existing = HighScore.query.filter_by(username=username).first()
    if existing:
        if score > existing.score:
            existing.score = score
    else:
        db.session.add(HighScore(username=username, score=score))

    db.session.commit()
    return jsonify({"msg": "Score submitted"}), 200

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    scores = HighScore.query.order_by(HighScore.score.desc()).limit(10).all()
    return jsonify([
        {"username": s.username, "score": s.score}
        for s in scores
    ])

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
