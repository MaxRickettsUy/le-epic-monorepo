from flask import current_app, url_for, request, redirect, flash,jsonify
import sqlalchemy as sa
from app import db
from app.models import Release, Band
from app.release import bp
import json

#TODO very future... get all by filter?

@bp.route('/new', methods=['POST',])
def create():
    band_id = request.args.get('band', 0, type=int)
    band = db.first_or_404(sa.select(Band).where(Band.id == band_id))

    json_data = request.get_json()
    name = json_data['name']
    length = json_data['length']
    art = json_data['art']
    release_type = json_data['release_type']

    release = Release(name=name,length=length,art=art,release_type=release_type,band=band)
    db.session.add(release)
    db.session.commit()
    return 'release created'

@bp.route('/<id>', methods=['GET',])
def get(id):
    print('getting a release...')
    release = db.first_or_404(sa.select(Release).where(Release.id == id))
    print(release.as_dict())
    return jsonify({'release': release.as_dict()})

@bp.route('/<id>/update', methods=['POST',])
def update(id):
    release = db.first_or_404(sa.select(Release).where(Release.id == id))
    json_data = request.get_json()
    release.name = json_data['name']
    release.status = json_data['length']
    release.band_picture = json_data['art']
    release.release_type = json_data['release_type']
    db.session.commit()
    return 'release update successful'

@bp.route('/<id>/delete', methods=['DELETE',])
def delete(id):
    release = db.first_or_404(sa.select(Release).where(Release.id == id))
    db.session.delete(release)
    db.session.commit()
    return 'release delete successful'