from flask import current_app, url_for, request, redirect, flash, jsonify
import sqlalchemy as sa
from app import db
from app.models import Band, Release
from app.band import bp
import json

#TODO general form validation

@bp.route('/')
@bp.route('/index')
def get_all():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Band)
    bands = db.paginate(query, page=page, per_page=current_app.config['BANDS_PER_PAGE'], error_out=False)
    next_url = url_for('band.get_all', page=bands.next_num) if bands.has_next else None
    prev_url = url_for('band.get_all', page=bands.prev_num) if bands.has_prev else None

    #TODO i dont like this but i think this is how it has to be bc im not passing response to render_template...
    band_list = []
    for band in bands.items:
        band_list.append(band.as_dict())
    return jsonify({'bands': band_list, 'next': next_url, 'prev': prev_url})

@bp.route('/new', methods=['POST',])
@login_required
def create():
    json_data = request.get_json()
    name = json_data['name']
    status = json_data['status']
    band_picture = json_data['band_picture']

    band = Band(name=name,status=status,band_picture=band_picture)
    db.session.add(band)
    db.session.commit()

    #TODO what return on successful create?
    return 'band created'

@bp.route('/<id>', methods=['GET',])
def get(id):
    band = db.first_or_404(sa.select(Band).where(Band.id == id))
    releases = db.session.execute(band.releases.select()).scalars()
    release_list = []
    for release in releases:
        review_count = release.reviews_count()
        avg_review = release.avg_review_score()
        release_list.append({
            'release': release.as_dict(),
            'review_count': review_count,
            'avg_review': avg_review
        })
    return jsonify({'band': band.as_dict(), 'releases': release_list})

@bp.route('/<id>/update', methods=['POST',])
@login_required
def update(id):
    band = db.first_or_404(sa.select(Band).where(Band.id == id))
    json_data = request.get_json()
    band.name = json_data['name']
    band.status = json_data['status']
    band.band_picture = json_data['band_picture']
    db.session.commit()
    #TODO what return on successful update?
    return 'band updated'

@bp.route('/<id>/delete', methods=['DELETE',])
@login_required
def delete(id):
    band = db.first_or_404(sa.select(Band).where(Band.id == id))
    db.session.delete(band)
    db.session.commit()
    #TODO what return on successful delete?
    return 'band deleted'



