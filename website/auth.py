from flask import Blueprint, render_template, request, flash, redirect, url_for
from website.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth  = Blueprint('auth', __name__)

@auth.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember = True)
                return redirect(url_for('views.home'))
            else:
                flash('Vitlaust lykilorð, reyndu aftur', category = 'error')
        else:
            flash('Netfang fannst ekki', category='error')
    return render_template("login.html", user = current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Netfang hefur nú þegar aðgang', category='error')
        elif len(email) < 4:
            flash('Netfang þarf að vera lengra en 3 stafir', category='error')
        elif len(first_name) < 2:
            flash('Fyrsta nafn þarf að vera lengra en 1 stafur', category='error')
        elif password1 != password2:
            flash('Lykilorð eru ekki eins', category='error')
        elif len(password1) < 9:
            flash('Lykilorð þarf að vera 9 stafir eða lengra', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1))
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user, remember=True)  

            flash('Aðgangur stofnaður!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)