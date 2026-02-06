from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

app = Flask(__name__)
app.secret_key = "annseva_secret"

# ---------------- CONFIG ---------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./database.db'

app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------------- FIXED ADMIN ---------------- #
ADMIN_PHONE = "9905364605"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")

# ---------------- MODELS ---------------- #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20), unique=True)
    role = db.Column(db.String(20))
    password = db.Column(db.String(200))


class FoodPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(100))
    quantity = db.Column(db.String(50))
    location = db.Column(db.String(200))
    image = db.Column(db.String(200))
    status = db.Column(db.String(20), default="Pending")
    donor_id = db.Column(db.Integer)
    price = db.Column(db.Integer)
    receiver_id = db.Column(db.Integer)


# ---------------- HOME ---------------- #
@app.route('/')
def home():
    return redirect('/login')


# ---------------- REGISTER ---------------- #
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_password = generate_password_hash(request.form['password'])

        user = User(
            name=request.form['name'],
            phone=request.form['phone'],
            role=request.form['role'],
            password=hashed_password
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

        # ADMIN LOGIN
        if phone == ADMIN_PHONE and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['role'] = 'admin'
            return redirect('/admin')

        # NORMAL USERS
        user = User.query.filter_by(phone=phone).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'donor':
                return redirect('/donor')
            elif user.role == 'volunteer':
                return redirect('/volunteer')
            else:
                return redirect('/receiver')

        return "Invalid credentials"

    return render_template('login.html')


# ---------------- PASSWORD RECOVERY ---------------- #
@app.route('/recover', methods=['GET', 'POST'])
def recover():
    if request.method == 'POST':
        phone = request.form['phone']
        user = User.query.filter_by(phone=phone).first()

        if user:
            # Generate temporary password
            temp_password = str(random.randint(100000, 999999))
            user.password = generate_password_hash(temp_password)
            db.session.commit()

            return f"Your temporary password is: {temp_password}"

        return "Phone number not found"

    return render_template('recover.html')


# ---------------- DONOR DASHBOARD ---------------- #
@app.route('/donor')
def donor_dashboard():
    if session.get('role') != 'donor':
        return redirect('/login')

    posts = FoodPost.query.filter_by(donor_id=session['user_id']).all()
    return render_template('donor_dashboard.html', posts=posts)


# ---------------- ADD FOOD ---------------- #
@app.route('/add_food', methods=['GET', 'POST'])
def add_food():
    if session.get('role') != 'donor':
        return redirect('/login')

    if request.method == 'POST':
        file = request.files['image']
        filename = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        post = FoodPost(
            food_name=request.form['food_name'],
            quantity=request.form['quantity'],
            location=request.form['location'],
            price=request.form['price'],
            donor_id=session['user_id'],
            image=filename
        )

        db.session.add(post)
        db.session.commit()
        return redirect('/donor')

    return render_template('add_food.html')


# ---------------- VOLUNTEER DASHBOARD ---------------- #
@app.route('/volunteer')
def volunteer_dashboard():
    if session.get('role') != 'volunteer':
        return redirect('/login')

    posts = FoodPost.query.filter_by(status="Pending").all()
    return render_template('volunteer_dashboard.html', posts=posts)


@app.route('/accept/<int:id>')
def accept_food(id):
    post = FoodPost.query.get(id)
    post.status = "Collected"
    db.session.commit()
    return redirect('/volunteer')


# ---------------- RECEIVER DASHBOARD ---------------- #
@app.route('/receiver')
def receiver_dashboard():
    if session.get('role') != 'receiver':
        return redirect('/login')

    posts = FoodPost.query.filter_by(status="Collected").all()
    return render_template('receiver_dashboard.html', posts=posts)


@app.route('/book/<int:id>')
def book_food(id):
    post = FoodPost.query.get(id)
    post.status = "Booked"
    post.receiver_id = session['user_id']
    db.session.commit()
    return redirect('/receiver')



# ---------------- ADMIN DASHBOARD ---------------- #
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')

    users = User.query.all()
    posts = FoodPost.query.all()

    return render_template(
        'admin_dashboard.html',
        users=users,
        posts=posts,
        total_users=len(users),
        total_posts=len(posts),
        pending_posts=FoodPost.query.filter_by(status="Pending").count(),
        collected_posts=FoodPost.query.filter_by(status="Collected").count(),
        booked_posts=FoodPost.query.filter_by(status="Booked").count()
    )


# ---------------- LOGOUT ---------------- #
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
