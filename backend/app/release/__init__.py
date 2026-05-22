from flask import Blueprint

bp = Blueprint('release', __name__, url_prefix='/release')

from app.release import routes