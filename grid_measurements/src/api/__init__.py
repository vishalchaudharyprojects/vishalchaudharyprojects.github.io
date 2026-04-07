from flask import Flask
from .routes import bp as typhoon_bp


def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(typhoon_bp, url_prefix='/api/typhoon')

    return app
