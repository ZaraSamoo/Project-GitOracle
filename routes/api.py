from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from extensions import db

api_bp = Blueprint("api_bp", __name__)


def resolve_html_url(repo):
    html_url = (repo.html_url or "").strip() if repo.html_url else ""
    if html_url:
        return html_url
    owner = (repo.owner or "").strip() if repo.owner else ""
    name = (repo.name or "").strip() if repo.name else ""
    if owner and name:
        return f"https://github.com/{owner}/{name}"
    return None


def _topics_by_repo_id(repo_ids):
    if not repo_ids:
        return {}
    from models import RepoTopic, RepositoryTopic

    rows = (
        db.session.query(RepositoryTopic.repo_id, RepoTopic.name)
        .join(RepoTopic, RepoTopic.topic_id == RepositoryTopic.topic_id)
        .filter(RepositoryTopic.repo_id.in_(repo_ids))
        .all()
    )
    topics_map = {repo_id: [] for repo_id in repo_ids}
    for repo_id, topic_name in rows:
        topics_map.setdefault(repo_id, []).append(topic_name)
    for repo_id in topics_map:
        topics_map[repo_id] = sorted(set(t for t in topics_map[repo_id] if t))
    return topics_map


def _serialize_repository(repo, topics_map):
    return {
        "repo_id": repo.repo_id,
        "github_id": repo.github_id,
        "owner": repo.owner,
        "name": repo.name,
        "full_name": repo.full_name,
        "description": repo.description,
        "stars": repo.stars,
        "forks": repo.forks,
        "language": repo.language,
        "topics": topics_map.get(repo.repo_id, []),
        "html_url": resolve_html_url(repo),
        "github_url": resolve_html_url(repo),
        "created_at": repo.created_at.isoformat() if repo.created_at else None,
    }


@api_bp.route("/users", methods=["GET"])
def get_users():
    from models import User

    users = User.query.order_by(User.created_at.desc()).limit(50).all()
    return jsonify(
        {
            "count": len(users),
            "users": [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                }
                for user in users
            ],
        }
    )


@api_bp.route("/repositories", methods=["GET"])
def get_repositories():
    from models import Repository

    repositories = Repository.query.order_by(Repository.stars.desc()).limit(100).all()
    topics_map = _topics_by_repo_id([repo.repo_id for repo in repositories])
    return jsonify(
        {
            "count": len(repositories),
            "repositories": [_serialize_repository(repo, topics_map) for repo in repositories],
        }
    )


@api_bp.route("/issues", methods=["GET"])
def get_issues():
    from models import Issue

    issues = Issue.query.filter_by(state="open").order_by(Issue.created_at.desc()).limit(100).all()
    return jsonify(
        {
            "count": len(issues),
            "issues": [
                {
                    "issue_id": issue.issue_id,
                    "github_issue_id": issue.github_issue_id,
                    "repo_id": issue.repo_id,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "complexity_score": float(issue.complexity_score)
                    if issue.complexity_score is not None
                    else None,
                    "estimated_time_hours": float(issue.estimated_time_hours)
                    if issue.estimated_time_hours is not None
                    else None,
                    "github_url": issue.github_url,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                }
                for issue in issues
            ],
        }
    )


@api_bp.route("/saved-projects", methods=["GET"])
def get_saved_projects():
    from models import Repository, SavedRepository

    try:
        # Get user_id from query params (e.g. /saved-projects?user_id=2)
        user_id = request.args.get("user_id", type=int)

        # fallback if not provided (safe default)
        if user_id is None:
            user_id = 1

        saved_projects = (
            db.session.query(Repository, SavedRepository)
            .join(SavedRepository, SavedRepository.repo_id == Repository.repo_id)
            .filter(SavedRepository.user_id == user_id)
            .order_by(SavedRepository.saved_at.desc())
            .all()
        )

        repo_ids = [repo.repo_id for repo, _ in saved_projects]
        topics_map = _topics_by_repo_id(repo_ids)

        return jsonify({
            "count": len(saved_projects),
            "saved_projects": [
                {
                    "user_id": saved.user_id,
                    **_serialize_repository(repo, topics_map),
                    "saved_at": saved.saved_at.isoformat() if saved.saved_at else None,
                }
                for repo, saved in saved_projects
            ],
        })

    except Exception as e:
        return jsonify({
            "count": 0,
            "saved_projects": [],
            "error": str(e)
        }), 500

@api_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    from models import Recommendation

    try:
        recommendations = Recommendation.query.order_by(Recommendation.score.desc()).limit(100).all()
    except SQLAlchemyError as error:
        return jsonify(
            {
                "count": 0,
                "recommendations": [],
                "warning": f"Recommendations unavailable: {str(error)}",
            }
        ), 200

    return jsonify(
        {
            "count": len(recommendations),
            "recommendations": [
                {
                    "rec_id": recommendation.rec_id,
                    "user_id": recommendation.user_id,
                    "issue_id": recommendation.issue_id,
                    "score": float(recommendation.score)
                    if recommendation.score is not None
                    else None,
                    "reason": recommendation.reason,
                    "generated_at": recommendation.generated_at.isoformat()
                    if recommendation.generated_at
                    else None,
                }
                for recommendation in recommendations
            ],
        }
    )


@api_bp.route("/search", methods=["GET", "POST"])
def search_repositories():
    from models import Repository

    payload = request.get_json(silent=True) if request.method == "POST" else None

    def _get_field(name, default=""):
        if payload and name in payload and payload.get(name) is not None:
            return str(payload.get(name)).strip()
        return request.args.get(name, default).strip()

    query = _get_field("keyword")
    if not query:
        query = _get_field("query")
    if not query:
        query = _get_field("q")

    language = _get_field("language")
    topic = _get_field("topic")

    stars_raw = None
    if payload and payload.get("stars") is not None:
        stars_raw = payload.get("stars")
    elif payload and payload.get("stars_gte") is not None:
        stars_raw = payload.get("stars_gte")
    elif request.args.get("stars_gte") is not None:
        stars_raw = request.args.get("stars_gte")
    elif request.args.get("min_stars") is not None:
        stars_raw = request.args.get("min_stars")

    stars_gte = None
    if stars_raw is not None and str(stars_raw).strip() != "":
        try:
            stars_gte = int(str(stars_raw).replace("+", "").strip())
        except ValueError:
            stars_gte = None

    sort = _get_field("sort", "stars").lower() or "stars"
    limit_raw = payload.get("limit") if payload and payload.get("limit") is not None else request.args.get("limit")
    try:
        limit = int(limit_raw) if limit_raw is not None else 20
    except ValueError:
        limit = 20
    limit = max(1, min(limit, 50))

    q = Repository.query

    # STRUCTURED FILTERS FIRST (index-friendly)
    if language:
        q = q.filter(Repository.language.ilike(language))

    if stars_gte is not None:
        q = q.filter(Repository.stars >= stars_gte)

    # TOPIC FILTER
    if topic:
        from models import RepositoryTopic, RepoTopic

        q = q.join(
            RepositoryTopic,
            Repository.repo_id == RepositoryTopic.repo_id
        ).join(
            RepoTopic,
            RepoTopic.topic_id == RepositoryTopic.topic_id
        ).filter(
            RepoTopic.name.ilike(f"%{topic}%")
        )

    # KEYWORD FILTER
    if query:
        pattern = f"%{query}%"
        q = q.filter(
            or_(
                Repository.full_name.ilike(pattern),
                Repository.description.ilike(pattern),
            )
        )

    if sort == "stars":
        q = q.order_by(Repository.stars.desc())
    else:
        q = q.order_by(Repository.stars.desc())

    repositories = q.limit(limit).all()

    topics_map = _topics_by_repo_id([r.repo_id for r in repositories])

    return jsonify({
        "count": len(repositories),
        "mode": "keyword" if query else "filtered",
        "results": [
            _serialize_repository(repo, topics_map)
            for repo in repositories
        ]
    })
