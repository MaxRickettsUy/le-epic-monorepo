from flask import Blueprint

bp = Blueprint('track', __name__, url_prefix='/track')

from app.track import routes