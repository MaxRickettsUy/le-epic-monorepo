from flask import current_app, url_for, request, redirect, flash
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
    bands = db.paginate(query, page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('band.index', page=bands.next_num) if bands.has_next else None
    prev_url = url_for('band.index', page=bands.prev_num) if bands.has_prev else None
    return {'bands': bands, 'next': next_url, 'prev': prev_url}

@bp.route('/', methods=('POST,'))
def create():
    name = request.form['name']
    status = request.form['status']
    band_picture = request.form['band_picture']

    band = Band(name=name,status=status,band_picture=band_picture)
    db.session.add(band)
    db.session.commit()
    return redirect(url_for('band.index'))

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
    return {'band': band.as_dict(), 'releases': release_list}

@bp.route('/<id>/update', methods=['POST',])
def update(id):
    band = db.first_or_404(sa.select(Band).where(Band.id == id))
    band.name = request.form['name']
    band.status = request.form['status']
    band.band_picture = request.form['band_picture']
    db.session.commit()
    return redirect(url_for('band.index'))

@bp.route('/<id>/delete', methods=['DELETE',])
def delete(id):
    band = db.first_or_404(sa.select(Band).where(Band.id == id))
    db.session.delete(band)
    db.session.commit()
    return redirect(url_for('band.index'))


