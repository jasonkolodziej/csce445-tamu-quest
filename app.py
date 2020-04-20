from flask import Flask, render_template, abort, request, session, url_for, redirect
from flask_session import Session
from services import STATGame, Question, uuid_url64, MILESTONE_BANK as Milestones, QUESTION_BANK as Bank
from config import Config as C


sess = Session()
 
app = Flask(__name__, instance_relative_config=False)
app.config.from_object('config.Config')
sess.init_app(app)

redis_session = C.SESSION_REDIS

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html.j2')

@app.route('/game')
@app.route('/game/<key>')
def game(key=None):
    current_game = None
    randomize_answers = True
    # try getting the session
    try:
        for k, v in session.items():
            print(f"session key: {k}, session value : {v}")
        # if 'game_id' in session:
        current_game = session['stat_game']
        current_game = STATGame.from_redis(current_game) if current_game else None

    # new session
    except KeyError as k:
        # start a new session
        current_game = STATGame(uuid_url64())
        # add the prompts of game selection
        current_game.new_game()
        randomize_answers = False
        print(f"Session not found, generating new session for user. as {current_game}")
    # on the current game being found
    else:
        print(f"current_game is : {current_game}")
        if key is not None:
            print('',key, '')
            # resolve the user's selection
            # TODO: add more relevant logic for milestones in
            current_game.resolve_user_choice(key, Bank, Milestones)

    finally:
        # tell redis of the game session
        print(f"telling redis game is : {current_game.to_redis()}")
        print(f"telling user game is : {current_game.to_user(randomize=randomize_answers)}")
        session['stat_game'] = current_game.to_redis()
        if current_game.next_milestone:
            print('*='*20)
            print("rendering milestone for user")
            print('=*'*20)
            return render_template('milestone.html.j2', milestone=current_game.next_milestone.to_user(), game=current_game.to_user(randomize=randomize_answers))
        return render_template('stat_game.html.j2', game=current_game.to_user(randomize=randomize_answers))


@app.route('/instructions')
def instructions():
    return render_template('how_to_play.html.j2')

if __name__ == "__main__":
    app.run(host='0.0.0.0')