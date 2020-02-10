from flask import Flask, render_template, abort
 
app = Flask(__name__)
 
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
 
@app.route('/product/<key>')
def product(key):
    product = PRODUCTS.get(key)
    if not product:
        abort(404)
    return render_template('game.html.j2', product=product)

if __name__ == "__main__":
    app.run(host='0.0.0.0')