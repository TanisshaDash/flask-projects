from flask import Flask, request, render_template, redirect, jsonify, make_response, session, url_for
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
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', '')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT Settings
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY', 'defaultjwtsecret')
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["JWT_COOKIE_SECURE"] = False  # True for production with HTTPS
app.config["JWT_COOKIE_CSRF_PROTECT"] = False


db = SQLAlchemy(app)
jwt = JWTManager(app)


# --- Models ---
class User(db.Model):
    __tablename__ = "user"   # this sets the table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

# --- Home Route ---
@app.route("/", methods=["GET"])
@jwt_required(optional=True)
def home():
    username = get_jwt_identity()
    if username:
        return render_template("index.html", username=username)
    return redirect(url_for('login'))


# --- Register Route ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if not request.is_json:
        return "Request must be in JSON format", 400

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return "Username and password required", 400
    if User.query.filter_by(username=username).first():
        return "Username already exists", 400
    if len(password) < 4:
        return "Password must be at least 4 characters", 400

    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))


# --- Login Route ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(identity=username)
    resp = jsonify({"msg": "Login successful"})
    resp.set_cookie("access_token_cookie", access_token, httponly=True)
    return resp  # Don't redirect from backend when using JS-based login


@app.route("/welcome")
@jwt_required()
def welcome():
    username = get_jwt_identity()
    return render_template("index.html", username=username)


@app.route("/logout", methods=["POST"])
def logout():
    resp = jsonify({"msg": "Logged out"})
    unset_jwt_cookies(resp)
    return resp


@app.route("/start_game", methods=["GET"])
@jwt_required()
def start_game():
    target = random.randint(1, 50)
    session["target"] = target
    session["attempts"] = 7
    session["game_over"] = False
    return redirect("/play_game")  # Redirects to game screen


@app.route("/play_game", methods=["GET", "POST"])
@jwt_required()
def play_game():
    if 'target' not in session:
        return redirect(url_for('welcome'))

    message = ""
    game_over = session.get('game_over', False)
    attempts = session.get('attempts', 0)

    if request.method == "POST":
        guess = request.form.get("guess", "").strip()
        if guess.lower() == 'q':
            session['game_over'] = True
            return redirect(url_for('leaderboard'))

        try:
            guess = int(guess)
            target = session.get('target')
            if not 1 <= guess <= 50:
                message = "Guess must be between 1 and 50."
            elif guess == target:
                message = "Correct! You guessed the number!"
                session['game_over'] = True
            elif guess < target:
                message = "Too low!"
            else:
                message = "Too high!"
            session['attempts'] -= 1
            if session['attempts'] <= 0 and not session['game_over']:
                message = "Game Over! No attempts left."
                session['game_over'] = True
        except ValueError:
            message = "Invalid input. Enter a number between 1 and 50 or 'q' to quit."

    return render_template(
        "game.html",
        message=message,
        attempts=session.get('attempts', 0),
        game_over=session.get('game_over', False)
    )


@app.route("/submit_score", methods=["POST"])
@jwt_required()
def submit_score():
    try:
        data = request.get_json()
        score = data.get("score")
        username = get_jwt_identity()
        if not username or score is None:
            return jsonify({"msg": "Missing username or score"}), 400
        new_score = HighScore(username=username, score=int(score))
        db.session.add(new_score)
        db.session.commit()
        return jsonify({"msg": "Score submitted successfully!"}), 200
    except Exception as e:
        return jsonify({"msg": "Error processing score submission", "error": str(e)}), 500


@app.route("/leaderboard", methods=["GET"])
@jwt_required()
def leaderboard():
    high_scores = db.session.query(
        HighScore.username, db.func.max(HighScore.score).label('high_score')
    ).group_by(HighScore.username).order_by(db.desc('high_score')).all()
    return render_template("leaderboard.html", high_scores=high_scores)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
