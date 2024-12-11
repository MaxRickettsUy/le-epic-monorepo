from flask import current_app, url_for, request, redirect, flash
import sqlalchemy as sa
from app import db
from app.models import Review, Release, User
from app.review import bp
import json

#TODO CRUD review stuff.. get, update, delete
#TODO very future... get all by filter?

@bp.route('/', methods=['POST',])
def create():
    #TODO can this be sent from the frontend?
    release = db.first_or_404(sa.select(Release).where(Release.id == id))

    #TODO update this with code that works
    #TODO should be login code that stores user info when they log in
    user = 'get me from cookies'

    score = request.form['score']
    review_text = request.form['review_text']

    review = Review(score=score,review_text=review_text,author=user,release=release)
    db.session.add(review)
    db.session.commit()
    #TODO on successful review creation it should return user back to the release that was reviewed?
    return redirect(url_for('release.index'))

@bp.route('/<id>', methods=['GET',])
def get(id):
    review = db.first_or_404(sa.select(Review).where(Review.id == id))
    return {'review': review.as_dict()}

@bp.route('/<id>/update', methods=['POST',])
def update(id):
    review = db.first_or_404(sa.select(Review).where(Review.id == id))
    review.name = request.form['score']
    review.status = request.form['review_text']
    db.session.commit()
    return redirect(url_for('review.index'))

@bp.route('/<id>/delete', methods=['DELETE',])
def delete(id):
    review = db.first_or_404(sa.select(Review).where(Review.id == id))
    db.session.delete(review)
    db.session.commit()
    #TODO when we delete a release, we should redirect back to the list of releases for the band
    #TODO talk about this design and make sure it sounds good
    return redirect(url_for('band.index'))