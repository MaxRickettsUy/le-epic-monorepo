from flask import current_app, url_for, request, redirect, flash
import sqlalchemy as sa
from app import db
from app.models import Track, Release
from app.track import bp
import json

#TODO CRUD review stuff.. get, update, delete
#TODO very future... get all by filter?
#TODO bulk add tracks

@bp.route('/', methods=['POST',])
def create():
    #TODO can this be sent from the frontend?
    release = db.first_or_404(sa.select(Release).where(Release.id == id))

    name = request.form['name']
    track_number = request.form['track_number']
    length = request.form['length']
    lyrics = request.form['lyrics']

    track = Track(name=name,track_number=track_number,length=length,lyrics=lyrics,release=release)
    db.session.add(track)
    db.session.commit()
    #TODO on successful track creation it should return user back to the release that owns the track?
    return redirect(url_for('release.index'))

@bp.route('/<id>', methods=['GET',])
def get(id):
    track = db.first_or_404(sa.select(Track).where(Track.id == id))
    return {'track': track.as_dict()}

@bp.route('/<id>/update', methods=['POST',])
def update(id):
    track = db.first_or_404(sa.select(Track).where(Track.id == id))
    track.name = request.form['score']
    track.track_number = request.form['track_number']
    track.length = request.form['length']
    track.lyrics = request.form['lyrics']
    db.session.commit()
    return redirect(url_for('track.index'))

@bp.route('/<id>/delete', methods=['DELETE',])
def delete(id):
    track = db.first_or_404(sa.select(Track).where(Track.id == id))
    db.session.delete(track)
    db.session.commit()
    #TODO when we delete a track, we should redirect back to the release it belonged to
    #TODO talk about this design and make sure it sounds good
    return redirect(url_for('release.index'))