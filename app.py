from flask import Flask, request, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
import random
from functools import wraps
from flask import session, redirect, url_for, flash

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:AR122506@localhost/bank_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    ssn = db.Column(db.String(11), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    account_number = db.Column(db.String(12), unique=True, nullable=True)
    balance = db.Column(db.Float, default=0.0)


# This is for sign up page
@app.route("/")
def index(): 
    return render_template("SignUp.html")


@app.route('/signup', methods=['POST'])
def signup_action(): 
    new_user = User(
        username=request.form.get('username'),
        first_name=request.form.get('first_name'),
        last_name=request.form.get('last_name'),
        ssn=request.form.get('ssn'),
        address=request.form.get('address'),
        phone=request.form.get('phone'),
        password=request.form.get('password'),
        is_approved=False
    )
    
    db.session.add(new_user)
    db.session.commit()
    return "<h1>Success!</h1><p>Your application is pending admin approval.</p>"


# This is for authentication and authorization.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'is_admin' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# This is for admin page
@app.route("/admin")
@login_required 
def admin_panel():
    
    if not session.get('is_admin'):
        return "<h1>Unauthorized</h1><p>You do not have permission to view this page.</p>", 403

    pending_users = User.query.filter_by(is_approved=False).all()
    return render_template("admin.html", pending_users=pending_users)


@app.route("/admin/approve/<int:user_id>")
def approve_user(user_id):
    user = User.query.get(user_id)
    user.is_approved = True
    db.session.commit()
    return redirect("/admin")


@app.route("/admin/delete/<int:user_id>")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect("/admin")



# This is for Login page
@app.route("/login", methods=['GET'])
def show_login():
    return render_template("login.html")

app.secret_key = 'key' 

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    
    if username == "admin" and password == "admin123":
        session['is_admin'] = True
        session['username'] = "Admin"
        return redirect('/admin')

    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        if user.is_approved:
            if not user.account_number:
                new_account = str(random.randint(1000000000, 9999999999))
                user.account_number = new_account
                db.session.commit()

            session['user_id'] = user.id
            return redirect('/dashboard')
        else:
            return "<h1>Pending Approval</h1>"
            
    return "Wrong Credentials"


# This is for Account Page
@app.route("/dashboard")
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if not user:
        return redirect('/logout')
    return render_template("account.html", user=user)


# This is for transfer page
@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        recipient_acc = request.form.get('recipient_account')
        amount = float(request.form.get('amount'))

        recipient = User.query.filter_by(account_number=recipient_acc).first()

        if not recipient:
            return "<h1>recipient account not found.</h1>"
        if user.balance < amount:
            return "<h1>Insufficient funds.</h1>"
        if recipient.id == user.id:
            return "<h1>You cannot send money to yourself.</h1>"

        
        user.balance -= amount
        recipient.balance += amount
        db.session.commit()

        return f"<h1>Sent ${amount} to {recipient.first_name}.</h1><a href='/dashboard'>Back</a>"

    return render_template("transfer.html")


# this is the deposit page
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        card_num = request.form.get('card_num')
        
        if amount > 0:
            user = User.query.get(session['user_id'])
            user.balance += amount
            db.session.commit()
            
            return redirect('/dashboard')

    return render_template("Deposit.html")


if __name__ == "__main__":
    app.run(debug=True)



