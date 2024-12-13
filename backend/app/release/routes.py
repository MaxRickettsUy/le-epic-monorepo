from flask import current_app, url_for, request, redirect, flash
import sqlalchemy as sa
from app import db
from app.models import Release, Band
from app.release import bp
import json

#TODO CRUD release stuff.. get, update, delete
#TODO very future... get all by filter?

@bp.route('/new', methods=['POST',])
def create():
    band_id = request.args.get('band', 0, type=int)
    band = db.first_or_404(sa.select(Band).where(Band.id == band_id))

    name = request.form['name']
    length = request.form['length']
    art = request.form['art']
    release_type = request.form['release_type']

    release = Release(name=name,length=length,art=art,release_type=release_type,band=band)
    db.session.add(release)
    db.session.commit()
    return redirect(url_for('band.index'))

@bp.route('/<id>', methods=['GET',])
def get(id):
    release = db.first_or_404(sa.select(Release).where(Release.id == id))
    return {'release': release.as_dict()}

@bp.route('/<id>/update', methods=['POST',])
def update(id):
    release = db.first_or_404(sa.select(Release).where(Release.id == id))
    release.name = request.form['name']
    release.status = request.form['length']
    release.band_picture = request.form['art']
    release.release_type = request.form['release_type']
    db.session.commit()
    return redirect(url_for('release.index'))

@bp.route('/<id>/delete', methods=['DELETE',])
def delete(id):
    release = db.first_or_404(sa.select(Release).where(Release.id == id))
    db.session.delete(release)
    db.session.commit()
    #TODO when we delete a release, we should redirect back to the list of releases for the band
    #TODO talk about this design and make sure it sounds good
    return redirect(url_for('band.index'))