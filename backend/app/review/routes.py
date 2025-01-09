from flask import current_app, url_for, request, redirect, flash, jsonify
import sqlalchemy as sa
from app import db
from app.models import Review, Release, User
from app.review import bp
import json

#TODO CRUD review stuff.. get, update, delete
#TODO very future... get all by filter?

@bp.route('/new', methods=['POST',])
def create():
    release_id = request.args.get('release', 0, type=int)
    release = db.first_or_404(sa.select(Release).where(Release.id == release_id))

    #TODO when user logs in it should store id in cookies or context or something... pull from there
    user_id = request.args.get('user', 0, type=int)
    user = db.first_or_404(sa.select(User).where(User.id == user_id))

    json_data = request.get_json()
    score = json_data['score']
    review_text = json_data['review_text']

    review = Review(score=score,review_text=review_text,author=user,release=release)
    db.session.add(review)
    db.session.commit()

    return 'review created'

@bp.route('/<id>', methods=['GET',])
def get(id):
    review = db.first_or_404(sa.select(Review).where(Review.id == id))
    return jsonify({'review': review.as_dict()})

@bp.route('/<id>/update', methods=['POST',])
def update(id):
    review = db.first_or_404(sa.select(Review).where(Review.id == id))
    json_data = request.get_json()
    review.name = json_data['score']
    review.review_text = json_data['review_text']
    db.session.commit()
    return 'review updated'

@bp.route('/<id>/delete', methods=['DELETE',])
def delete(id):
    review = db.first_or_404(sa.select(Review).where(Review.id == id))
    db.session.delete(review)
    db.session.commit()
    return 'review deleted'