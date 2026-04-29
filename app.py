from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db, migrate
from routes.api import api_bp

# ----------------------------
# App Factory
# ----------------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # bind extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # import models AFTER db init (IMPORTANT)
    with app.app_context():
        import models
    app.register_blueprint(api_bp, url_prefix="/api")

    return app


# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == '__main__':
    app = create_app()
    print("InternHub Backend Running on http://127.0.0.1:5000")
    app.run(debug=True)