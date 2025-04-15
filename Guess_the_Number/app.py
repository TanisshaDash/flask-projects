from flask import Flask, render_template, request, redirect, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import random

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('GUESS_DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "default-secret")
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_COOKIE_SECURE'] = False  # For development only
app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

db = SQLAlchemy(app)
jwt = JWTManager(app)


@app.route("/debug_users")
def debug_users():
    users = User.query.all()
    return jsonify([{ "id": u.id, "username": u.username } for u in users])

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

# Routes
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        print(f"Registering: {username}, {password}")  # Debug

        # Check if the user already exists
        if User.query.filter_by(username=username).first():
            print("Username already exists.")
            return "Username already exists. Try another."

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        print("User saved!")

        return redirect("/login")

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # POST request from JavaScript fetch or form
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
    else:
        # If sent as form-data
        username = request.form.get('username')
        password = request.form.get('password')

    print("Login data:", {'username': username, 'password': password})

    user = User.query.filter_by(username=username).first()
    print("Found user:", user)

    if user and check_password_hash(user.password, password):
        token = create_access_token(identity=username)
        return jsonify(access_token=token)

    return jsonify({"message": "Invalid credentials"}), 401


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




@app.route('/submit_score', methods=['POST'])
@jwt_required()  # This decorator ensures the user is authenticated
def submit_score():
    current_user = get_jwt_identity()  # Get the user identity (username)
    score = request.json.get('score')
    
    # Save the score to the database or perform some action
    return jsonify({"message": f"Score submitted successfully by {current_user}"})




@app.route("/leaderboard")
def leaderboard():
    scores = HighScore.query.order_by(HighScore.score.desc()).all()
    return render_template("leaderboard.html", scores=scores)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
