from flask import current_app, url_for, request, redirect, flash, jsonify
import sqlalchemy as sa
from app import db
from app.models import User
from app.user import bp
import json
from flask_login import current_user, login_user, logout_user

#TODO build out actual auth endpoints (which i think will all live in auth endpoint folder but wanted to make a note here)
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return '' #redirect to index if already logged in
    json_data = request.get_json()
    username = json_data['username']
    password = json_data['password']
    remember_me = json_data['remember_me']

    user = db.session.scalar(
        sa.select(User).where(User.username == username)
    )

    if user is None or not user.check_password(password):
        return 'invalid' #invalid username or password

    login_user(user, remember=remember_me)
    return 'logged in'

@bp.route('/logout')
def logout():
    logout_user()
    return 'logged out'

#TODO create may get moved to auth? or might invoke something from auth idk
#just have to do some sort of pass hashing when a user is created
@bp.route('/new', methods=['POST',])
def create():
    json_data = request.get_json()
    username = json_data['username']
    email = json_data['email']
    password = json_data['password']

    #TODO some step here to hash the password

    user = User(username=username,email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return 'user created'

@bp.route('/<id>', methods=['GET',])
@login_required
def get(id):
    user = db.first_or_404(sa.select(User).where(User.id == id))
    return jsonify({'user': user.as_dict()})

#TODO account for user pass update, need to make sure re hash occurs so no plain text storage
@bp.route('/<id>/update', methods=['POST',])
@login_required
def update(id):
    user = db.first_or_404(sa.select(User).where(User.id == id))
    json_data = request.get_json()
    user.username = json_data['username']
    user.email = json_data['email']
    if json_data['password_hash'] is not None:
        #hash the password
        password_hash = 'function that returns a hashed pass'
        user.password_hash = password_hash
    db.session.commit()
    return 'user updated'

@bp.route('/<id>/delete', methods=['DELETE',])
@login_required
def delete(id):
    user = db.first_or_404(sa.select(User).where(User.id == id))
    db.session.delete(user)
    db.session.commit()
    return 'user deleted'