from flask import Blueprint

bp = Blueprint('release', __name__)

from app.release import routes