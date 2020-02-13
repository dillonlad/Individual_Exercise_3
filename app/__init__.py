from flask import Flask, render_template
from config import DevConfig


def create_app(config_class=DevConfig):
    """
    Creates an application instance to run
    :return: A Flask object
    """

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register Blueprints
    from routes import bp_main
    app.register_blueprint(bp_main)

    return app
