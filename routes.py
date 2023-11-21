from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import User, db
from app import app

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        return render_template('index.html')

@app.route('/signup', methods = ['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        roles = ['Creator', 'Listener']
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = roles[int(request.form.get('role')) - 1]

        if username == '' or name == '' or password == '' or confirm_password == '':
            flash('Please fill out all fields', '')
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match', 'info')
            return redirect(url_for('signup'))

        user = User.query.filter_by(username=username).first()
        if user is not None:
            flash('Username already exists', 'info')
            return redirect(url_for('signup'))

        new_user = User(username=username, password=password, name=name, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    else:
        return render_template('signup.html')


@app.route('/login', methods = ['POST','GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('Username does not exist', 'info')
            return redirect(url_for('login'))
        elif not user.verify_password(password):
            flash('Incorrect password', 'info')
            return redirect(url_for('login'))
        else:
            session['user_id'] = user.id
            return redirect(url_for('index'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('profile.html', user=user)

@app.route('/change_password', methods = ['GET','POST'])
def change_password():
    user = User.query.filter_by(id=session['user_id']).first()
    old_password = request.form.get('old_password')

    if not user.verify_password(old_password):
        flash('Incorrect password', 'info')
        return redirect(url_for('profile'))

    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    if new_password != confirm_password:
        flash('Passwords do not match', 'info')
        return redirect(url_for('profile'))

    user.password = new_password
    db.session.commit()
    flash('Password changed', 'info')
    return redirect(url_for('profile'))

@app.route('/become_creator', methods=['GET','POST'])
def become_creator():
    user = User.query.filter_by(id=session['user_id']).first()
    user.role = 'Creator'
    db.session.commit()
    flash('You are now a creator', 'info')
    return redirect(url_for('profile'))

@app.route('/uploads')
def uploads():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        user = User.query.filter_by(id=session['user_id']).first()
        return render_template('uploads.html', user=user)

