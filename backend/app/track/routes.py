from flask import current_app, url_for, request, redirect, flash,jsonify
import sqlalchemy as sa
from app import db
from app.models import Track, Release
from app.track import bp
import json

#TODO bulk create tracks
@bp.route('/new', methods=['POST',])
def create():
    release_id = request.args.get('release', 0, type=int)
    release = db.first_or_404(sa.select(Release).where(Release.id == release_id))

    json_data = request.get_json()
    name = json_data['name']
    track_number = json_data['track_number']
    length = json_data['length']
    lyrics = json_data['lyrics']

    track = Track(name=name,track_number=track_number,length=length,lyrics=lyrics,release=release)
    db.session.add(track)
    db.session.commit()

    return 'track created'

@bp.route('/<id>', methods=['GET',])
def get(id):
    track = db.first_or_404(sa.select(Track).where(Track.id == id))
    return jsonify({'track': track.as_dict()})

@bp.route('/<id>/update', methods=['POST',])
def update(id):
    track = db.first_or_404(sa.select(Track).where(Track.id == id))
    json_data = request.get_json()
    track.name = json_data['name']
    track.track_number = json_data['track_number']
    track.length = json_data['length']
    track.lyrics = json_data['lyrics']
    db.session.commit()
    return 'track updated'

@bp.route('/<id>/delete', methods=['DELETE',])
def delete(id):
    track = db.first_or_404(sa.select(Track).where(Track.id == id))
    db.session.delete(track)
    db.session.commit()
    return 'track deleted'