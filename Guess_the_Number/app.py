from flask import Flask, render_template, request, redirect, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash
import random
import os
from dotenv import load_dotenv
from datetime import timedelta


load_dotenv()
app = Flask(__name__)

# Configs
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('GUESS_DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'supersecretkey')
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

# Routes
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_pw = generate_password_hash(password)

        if User.query.filter_by(username=username).first():
            return "Username already exists."

        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            access_token = create_access_token(identity=username)
            response = make_response(redirect("/"))
            response.set_cookie(
                "access_token_cookie",
                access_token,
                max_age=timedelta(days=1),
                httponly=True
            )
            return response
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    response = make_response(redirect("/login"))
    unset_jwt_cookies(response)
    return response

@app.route("/", methods=["GET", "POST"])
@jwt_required()
def home():
    username = get_jwt_identity()
    if request.method == "POST":
        target = random.randint(1, 50)
        attempts = 7
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=False)
    return render_template("index.html", username=username)

@app.route("/play_game", methods=["POST"])
@jwt_required()
def play_game():
    username = get_jwt_identity()
    target = int(request.form["target"])
    guess = request.form["guess"]
    attempts = int(request.form["attempts"])

    if guess.lower() == "q":
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=True, message="You quit the game!")

    try:
        guess = int(guess)
    except ValueError:
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=False, message="Invalid input! Enter a number.")

    if guess == target:
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=True, message="CORRECT GUESS!!!")

    attempts -= 1
    if attempts == 0:
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=True, message=f"Game Over! The correct number was {target}.")

    feedback = "Number too SMALL" if guess < target else "Number too BIG"
    return render_template("game.html", username=username, target=target, attempts=attempts, game_over=False, message=feedback)

@app.route("/submit_score", methods=["POST"])
@jwt_required()
def submit_score():
    username = get_jwt_identity()
    attempts = int(request.form["attempts"])

    existing_score = HighScore.query.filter_by(username=username).first()
    if existing_score:
        if attempts > existing_score.score:
            existing_score.score = attempts
    else:
        db.session.add(HighScore(username=username, score=attempts))
    db.session.commit()

    return redirect("/leaderboard")

@app.route("/leaderboard")
def leaderboard():
    scores = HighScore.query.order_by(HighScore.score.desc()).all()
    return render_template("leaderboard.html", scores=scores)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
