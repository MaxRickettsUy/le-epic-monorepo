from flask import Blueprint

bp = Blueprint('band', __name__, url_prefix='/band')

from app.band import routes