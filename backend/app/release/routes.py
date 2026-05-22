from flask import current_app, url_for, request, redirect, flash,jsonify
import sqlalchemy as sa
from app import db
from app.models import Release, Band, Track
from app.release import bp
import json
from sqlalchemy.orm import joinedload

#TODO very future... get all by filter?

@bp.route('/new', methods=['POST',])
# @login_required
def create():
    band_id = request.args.get('band', 0, type=int)
    band = db.first_or_404(sa.select(Band).where(Band.id == band_id))

    json_data = request.get_json()
    name = json_data['name']
    length = json_data['length']
    art = json_data['art']
    release_type = json_data['release_type']
    label = json_data['label']
    year = json_data['year']

    release = Release(
        name=name,
        length=length,
        art=art,
        release_type=release_type,
        band=band,
        label=label,
        year=year
    )
    db.session.add(release)
    db.session.commit()
    return jsonify({"message": "Release created"}), 200


@bp.route('/<id>', methods=['GET',])
def get(id):
    # 1) Load the Release and its Band (but NOT tracks via joinedload)
    release = (
        Release.query
        .options(joinedload(Release.band))
        .get_or_404(id)
    )

    # 2) Manually fetch all Track rows for this release
    #    (adjust `position` if you store track order differently)
    tracks = (
        Track.query
        .filter_by(release_id=release.id)
        .order_by(Track.position)
        .all()
    )

    # 3) Build a list of track dictionaries
    tracks_list = []
    for t in tracks:
        tracks_list.append({
            'id': t.id,
            'title': t.title,
            'length': t.length,
            'position': t.position
        })

    # 4) Return nested JSON including band + tracks
    return jsonify({
        'id': release.id,
        'name': release.name,
        'length': release.length,
        'release_type': release.release_type,
        'band_id': release.band_id,
        'mbid': release.mbid,
        'band': {
            'id': release.band.id,
            'name': release.band.name,
            'location': release.band.location,
            'country': release.band.country,
            'label': release.band.label
        },
        'tracks': tracks_list
    })


@bp.route('/<id>/update', methods=['POST',])
# @login_required
def update(id):
    release = db.first_or_404(sa.select(Release).where(Release.id == id))
    json_data = request.get_json()
    release.name = json_data['name']
    release.status = json_data['length']
    release.band_picture = json_data['art']
    release.release_type = json_data['release_type']
    release.label = json_data['label']
    release.year = json_data['year']
    db.session.commit()
    return 'release update successful'

@bp.route('/<id>/delete', methods=['DELETE',])
# @login_required
def delete(id):
    release = db.first_or_404(sa.select(Release).where(Release.id == id))
    db.session.delete(release)
    db.session.commit()
    return 'release delete successful'