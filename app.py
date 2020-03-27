from flask import Flask, render_template, abort, request, session
from flask_session import Session
from services import STATGame, uuid_url64
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
    # if request.method == 'POST':

    # if 'game_id' in session:
    #     # find the game object in the DB
    #     pass
    # else:
    #     # this is a new game
    #     session['game_id'] = uuid_url64();
        # create class
        # store in DB
        # render the options for the user
    if key is not None:
        print(key)
    return render_template('stat_game.html.j2', prompt=STATGame.level_selector_prompt(), answer_choices=STATGame.level_types(), answerType=COLORS)


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