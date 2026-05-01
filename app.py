from flask import Flask
from flask_cors import CORS
from sqlalchemy import text
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
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_repo_language ON repositories(language)")
        )
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_repo_stars ON repositories(stars)")
        )
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_repo_topics_name ON repo_topics(name)")
        )
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_repo_topics_repo_id ON repository_topics(repo_id)")
        )
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_saved_user ON saved_repositories(user_id)")
        )
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_saved_repo ON saved_repositories(repo_id)")
        )
        db.session.execute(
            text("CREATE INDEX IF NOT EXISTS idx_saved_user_repo ON saved_repositories(user_id, repo_id)")
        )
        db.session.commit()
    app.register_blueprint(api_bp, url_prefix="/api")

    return app


# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == '__main__':
    app = create_app()
    print("InternHub Backend Running on http://127.0.0.1:5000")
    app.run(debug=True)