from app import create_app, db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import Band, User, Release, Track, Review

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Band': Band, 'Release': Release, 'Track': Track, 'Review': Review}