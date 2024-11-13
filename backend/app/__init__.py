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
    migrate.init_app(app)

    #TODO implement and register auth bp

    from app.band import bp as band_bp
    app.register_blueprint(band_bp)

    from app.user import bp as user_bp
    app.register_blueprint(user_bp)
    
    return app