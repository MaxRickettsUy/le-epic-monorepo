from flask import Blueprint

bp = Blueprint('track', __name__)

from app.track import routes