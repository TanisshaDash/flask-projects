from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///high_scores.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    score = db.Column(db.Integer, nullable=False)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form["username"]
        target = random.randint(1, 50)
        attempts = 7
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=False)
    return render_template("index.html")



@app.route("/submit_score", methods=["POST"])
def submit_score():
    username = request.form["username"]
    attempts = int(request.form["attempts"])

    with app.app_context():
        existing_score = HighScore.query.filter_by(username=username).first()
        if existing_score:
            if attempts > existing_score.score:  # Save only if it's a higher score
                existing_score.score = attempts
                db.session.commit()
        else:
            new_score = HighScore(username=username, score=attempts)
            db.session.add(new_score)
            db.session.commit()
    
    return redirect("/leaderboard")
@app.route("/leaderboard")
def leaderboard():
    scores = HighScore.query.order_by(HighScore.score.desc()).all()  
    return render_template("leaderboard.html", scores=scores)



@app.route("/play_game", methods=["POST"])
def play_game():
    username = request.form["username"]
    target = int(request.form["target"])
    guess = request.form["guess"]
    attempts = int(request.form["attempts"])
    
    if guess.lower() == "q":
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=True, message="You quit the game!")

    try:
        guess = int(guess)
    except ValueError:
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=False, message="Invalid input!Enter a number.")

    if guess == target:
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=True, message="CORRECT GUESS!!!")

    attempts -= 1
    if attempts == 0:
        return render_template("game.html", username=username, target=target, attempts=attempts, game_over=True, message=f"Game Over! The correct number was {target}.")

    feedback = "Number too SMALL" if guess < target else "Number too BIG"
    return render_template("game.html", username=username, target=target, attempts=attempts, game_over=False, message=feedback)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
