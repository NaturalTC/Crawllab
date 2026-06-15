from flask import Flask
from datetime import timedelta
from .config import Config
from .extensions import jwt, cors, init_mongo


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)

    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
    init_mongo(app)

    from .auth.routes import auth_bp
    from .jobs.routes import jobs_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")

    return app
