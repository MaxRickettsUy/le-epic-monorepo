from flask import Blueprint

bp = Blueprint('release', __name__, '/release')

from app.release import routes