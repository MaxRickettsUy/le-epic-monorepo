from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

#initializing dependencies
db = SQLAlchemy()
migrate = Migrate()

#integrate all dependencies with app and spin up flask app
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    #TODO implement and register auth bp

    from app.band import bp as band_bp
    app.register_blueprint(band_bp)

    from app.user import bp as user_bp
    app.register_blueprint(user_bp)

    from app.release import bp as release_bp
    app.register_blueprint(release_bp)

    from app.review import bp as review_bp
    app.register_blueprint(review_bp)

    from app.track import bp as track_bp
    app.register_blueprint(track_bp)
    
    return app

from app import models