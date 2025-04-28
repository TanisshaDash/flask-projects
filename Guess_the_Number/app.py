from flask import Flask, request, render_template, redirect, jsonify, make_response,session,url_for
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
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///guess_game.db'
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

    # Store username in session for tracking
    session['username'] = user.username
    
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
    print("Start Game route hit!") 
    # Generate a random target and set the number of attempts
    target = random.randint(1, 50)
    attempts = 7  # Set attempts to 7

    # Store the game state in the session
    session["target"] = target
    session["attempts"] = attempts
    session["game_over"] = False  # Keep track if the game is over or not
    
     # Redirect to the /play_game route
    return redirect("/play_game")


@app.route("/play_game", methods=["GET", "POST"])
def play_game():
    if 'target' not in session:
        return redirect(url_for('index'))

    message = ""
    game_over = session.get('game_over', False)
    attempts = session.get('attempts', 5)

    if request.method == "POST":
        guess = request.form.get("guess")
        
        if guess is None:
            guess = ""

        if guess.lower() == 'q':
            # User wants to quit
            session['game_over'] = True
            return redirect(url_for('leaderboard'))

        # Otherwise normal number guess
        try:
            guess = int(guess)
            target = session.get('target')
            if guess > 50:
                return jsonify({"msg": "Invalid number. Please guess a number between 1 and 50."}), 400
            
            if guess == target:
                message = "Correct! You guessed the number!"
                session['game_over'] = True
            elif guess < target:
                message = "Too low!"
            else:
                message = "Too high!"
            
            session['attempts'] -= 1

            if session['attempts'] <= 0:
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
def submit_score():
    if 'username' not in session:
        return jsonify({"msg": "User not logged in"}), 401
    
    # Rest of the code...

    try:
        # Get the score from the request body
        data = request.get_json()  # This retrieves the JSON sent from the frontend

        # Check if the score is in the received JSON data
        score = data.get("score")
        username = session.get('username')  # Get username from session

        if not username or not score:
            return jsonify({"msg": "Missing username or score"}), 400

        # Store the score in the database
        new_score = HighScore(username=username, score=int(score))
        db.session.add(new_score)
        db.session.commit()

        return jsonify({"msg": "Score submitted successfully!"}), 200  # Success message

    except Exception as e:
        return jsonify({"msg": "Error processing the score submission", "error": str(e)}), 500




@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to home page if user is not logged in

    # Query to get the highest score for each user
    high_scores = db.session.query(
        HighScore.username, db.func.max(HighScore.score).label('high_score')
    ).group_by(HighScore.username).order_by(db.desc('high_score')).all()

    return render_template("leaderboard.html", high_scores=high_scores)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
