from flask import Blueprint

bp = Blueprint('review', __name__, url_prefix='/review')

from app.review import routes