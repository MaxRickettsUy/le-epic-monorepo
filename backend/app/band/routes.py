from flask import current_app, url_for, request, redirect, flash, jsonify
import sqlalchemy as sa
from app import db
from app.models import Band, Release
from app.band import bp
import json

import musicbrainzngs

musicbrainzngs.set_useragent("Hardchives","0.1","mrucoding@gmail.com")
musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

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
# @login_required
def create():
    json_data = request.get_json()
    name = json_data['name']
    status = json_data['status']
    band_picture = json_data['band_picture']
    location = json_data['location']
    country = json_data['country']
    label = json_data['label']

    band = Band(
        name=name,
        status=status,
        band_picture=band_picture,
        location=location,
        country=country,
        label=label
    )
    db.session.add(band)
    db.session.commit()

    #TODO what return on successful create?
    return jsonify({ "message": 'Band created', 'id': band.id }), 200

@bp.route('/<id>', methods=['GET',])
def get(id):
    band = db.first_or_404(sa.select(Band).where(Band.id == id))
    releases = db.session.execute(band.releases.select()).scalars()
    release_list = []

    for release in releases:
        review_count = release.reviews_count()
        avg_review = release.avg_review_score()
        release_list.append({
            **release.as_dict(), # spread attrs
            'review_count': review_count,
            'avg_review': avg_review
        })

    return jsonify({
        **band.as_dict(),
        'releases': release_list
    })

@bp.route('/<id>/update', methods=['POST',])
# @login_required
def update(id):
    band = db.first_or_404(sa.select(Band).where(Band.id == id))
    json_data = request.get_json()
    band.name = json_data['name']
    band.status = json_data['status']
    band.band_picture = json_data['band_picture']
    band.location = json_data['location']
    band.country = json_data['country']
    db.session.commit()
    #TODO what return on successful update?
    return 'band updated'

@bp.route('/<id>/delete', methods=['DELETE',])
# @login_required
def delete(id):
    band = db.first_or_404(sa.select(Band).where(Band.id == id))
    db.session.delete(band)
    db.session.commit()
    #TODO what return on successful delete?
    return 'band deleted'

@bp.route('/search', methods=['GET'])
def search_artist():
    name = request.args.get('name')
    # hardcore = request.args.get('hardcore', '').lower() in ['1', 'true']
    if not name:
        return jsonify({'error': "Missing required 'name' parameter"}), 400

    query = f'artist:"{name}"'
    # if hardcore:
    query = f'tag:hardcore-punk AND {query}'

    try:
        result = musicbrainzngs.search_artists(query=query, limit=10)
    except musicbrainzngs.WebServiceError as e:
        return jsonify({'error': 'MusicBrainz API error', 'details': str(e)}), 503

    return jsonify(result)

@bp.route('/search_releases', methods=['GET'])
def search_releases():
    name = request.args.get('name')
    if not name:
        return jsonify({'error': "Missing required 'name' parameter"}), 400

    # 1. Find the artist
    artist_result = musicbrainzngs.search_artists(query=f'artist:"{name}"', limit=1)
    artists = artist_result.get('artist-list', [])
    if not artists:
        return jsonify({'error': 'Band not found'}), 404

    mbid = artists[0]['id']

    # 2. Fetch tags and determine hardcore status
    artist_info = musicbrainzngs.get_artist_by_id(mbid, includes=['tags'])
    tags = [t['name'].lower() for t in artist_info['artist'].get('tag-list', [])]
    allowed = {'hardcore-punk', 'hardcore', 'punk', 'punk rock', 'post-hardcore'}
    is_not_hc = not any(g in tags for g in allowed)

    # 3. Browse all releases for this artist
    releases_response = musicbrainzngs.browse_releases(
        artist=mbid,
        includes=['release-groups'],
        limit=100
    )

    # 4. Return releases plus flag
    return jsonify({
        'isNotHardcore': is_not_hc,
        'releases': releases_response.get('release-list', [])
    })