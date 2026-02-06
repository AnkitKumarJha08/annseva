from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "annseva_secret"

# ---------------- DATABASE ---------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------------- MODELS ---------------- #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20))
    password = db.Column(db.String(50))

class FoodPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(100))
    quantity = db.Column(db.String(50))
    location = db.Column(db.String(200))
    image = db.Column(db.String(200))
    status = db.Column(db.String(20), default="Pending")
    donor_id = db.Column(db.Integer)

# ---------------- HOME ---------------- #
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ---------------- #
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            name=request.form['name'],
            phone=request.form['phone'],
            role=request.form['role'],
            password=request.form['password']
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

# ---------------- LOGIN ---------------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']

        user = User.query.filter_by(phone=phone, password=password).first()

        if user:
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'donor':
                return redirect('/donor')
            else:
                return redirect('/volunteer')
        else:
            return "Invalid phone or password"

    return render_template('login.html')

# ---------------- DONOR DASHBOARD ---------------- #
@app.route('/donor')
def donor_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('donor_dashboard.html')

# ---------------- ADD FOOD ---------------- #
@app.route('/add_food', methods=['GET', 'POST'])
def add_food():
    if request.method == 'POST':
        food_name = request.form['food_name']
        quantity = request.form['quantity']
        location = request.form['location']
        donor_id = session['user_id']

        post = FoodPost(
            food_name=food_name,
            quantity=quantity,
            location=location,
            donor_id=donor_id
            
        )
        post.status = "Pending"

        db.session.add(post)
        db.session.commit()

        return redirect('/donor')

    return render_template('add_food.html')

# ---------------- VOLUNTEER DASHBOARD ---------------- #
@app.route('/volunteer')
def volunteer_dashboard():
    posts = FoodPost.query.filter_by(status="Pending").all()
    return render_template('volunteer_dashboard.html', posts=posts)


# ---------------- ACCEPT FOOD ---------------- #
@app.route('/accept/<int:id>')
def accept_food(id):
    post = FoodPost.query.get(id)
    post.status = "Picked"
    db.session.commit()
    return redirect('/volunteer')
# -------- MARK AS COLLECTED --------
@app.route('/collected/<int:id>')
def collected_food(id):
    post = FoodPost.query.get(id)
    post.status = "Collected"
    db.session.commit()
    return redirect('/volunteer')

# ---------------- LOGOUT ---------------- #
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- MAIN ---------------- #
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
