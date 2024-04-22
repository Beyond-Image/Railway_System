from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in Successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect Password, Try Again.', category='error')
        else:
            flash('Incorrect User Email, Try Again.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have Logged Out', category='success')
    return redirect(url_for('views.home'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        email=request.form.get('email')
        FirstName=request.form.get('FirstName')
        LastName=request.form.get('LastName')
        password1=request.form.get('password1')
        password2=request.form.get('password2')
        street_address=request.form.get('address')
        zipcode=request.form.get('zipcode')
        state=request.form.get('state')
        city=request.form.get('city')
        ethnic=request.form.get('ethnic')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email Already In User.', category='error')
        elif password1 != password2:
            flash('Passwords Don\'t Match', category='error')
        elif(len(email) < 5):
            flash('email too short', category='error')
        elif(len(FirstName) == 0):
            flash('Please Enter First Name', category='error')
        elif(len(LastName) == 0):
            flash('Please Enter Last Name', category='error')
        else:
            new_user = User(email=email, password=generate_password_hash(password1),
                            firstname=FirstName, lastname=LastName, role='user',
                            address_street=street_address, address_zipcode=zipcode,
                            address_state=state, address_city=city, ethnicity=ethnic)
            db.session.add(new_user)
            db.session.commit()
            flash('Account Created', category='success')
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))

    return render_template("signup.html", user=current_user)

@auth.route('/adminman', methods=['GET', 'POST'])
def adminman():
    if request.method == "POST":
        email=request.form.get('email')
        FirstName=request.form.get('firstname')
        LastName=request.form.get('lastname')
        password1=request.form.get('password1')
        password2=request.form.get('password2')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email Already In User.', category='error')
        elif password1 != password2:
            flash('Passwords Don\'t Match', category='error')
        elif(len(email) < 5):
            flash('email too short', category='error')
        else:
            new_user = User(email=email, password=generate_password_hash(password1), 
                            firstname=FirstName, lastname=LastName, role='admin')
            
            db.session.add(new_user)
            db.session.commit()
            flash('Account Created', category='success')
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))

    return render_template("adminman.html", user=current_user)