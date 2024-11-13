from flask import Blueprint

bp = Blueprint('band', __name__)

from app.band import routes