from flask import Flask, render_template, abort, request, session
from flask_session import Session
from services import STATGame, Question, uuid_url64, QUESTION_BANK as Bank
from config import Config as C


sess = Session()
 
app = Flask(__name__, instance_relative_config=False)
app.config.from_object('config.Config')
sess.init_app(app)

redis_session = C.SESSION_REDIS

PRODUCTS = {
    'iphone': {
        'name': 'iPhone 5S',
        'category': 'Phones',
        'price': 699,
    },
    'galaxy': {
        'name': 'Samsung Galaxy 5',
        'category': 'Phones',
        'price': 649,
    },
    'ipad-air': {
        'name': 'iPad Air',
        'category': 'Tablets',
        'price': 649,
    },
    'ipad-mini': {
        'name': 'iPad Mini',
        'category': 'Tablets',
        'price': 549
    }
}

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html.j2', products=PRODUCTS)

COLORS = {
    'Right' : 'green',
    'Wrong' : 'red'
}


@app.route('/game')
@app.route('/game/<key>')
def game(key=None):
    current_game = None

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
        print(f"Session not found, generating new session for user. as {current_game}")
    # on the current game being found
    else:
        print(f"current_game is : {current_game}")
        if key is not None:
            print('',key, '')
            # resolve the user's selection
            current_game.resolve_user_choice(key, Bank)
    finally:
        # tell redis of the game session
        print(f"telling redis game is : {current_game.to_redis()}")
        print(f"telling user game is : {current_game.to_user()}")
        session['stat_game'] = current_game.to_redis()
        return render_template('stat_game.html.j2', game=current_game.to_user())


@app.route('/instructions')
def instructions():
    return render_template('how_to_play.html.j2')
 
@app.route('/product/<key>')
def product(key):
    product = PRODUCTS.get(key)
    if not product:
        abort(404)
    return render_template('game.html.j2', product=product)

if __name__ == "__main__":
    app.run(host='0.0.0.0')