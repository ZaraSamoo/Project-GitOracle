from flask import Blueprint, jsonify, request
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


def _serialize_repository(repo, topics_map, difficulty_score=None):
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
        "difficulty_score": difficulty_score,
        "created_at": repo.created_at.isoformat() if repo.created_at else None,
    }


def _extract_user_id_from_request():
    user_id = request.args.get("user_id", type=int)
    if user_id:
        return user_id

    header_user_id = request.headers.get("X-User-Id")
    if header_user_id:
        try:
            parsed = int(header_user_id)
            if parsed > 0:
                return parsed
        except ValueError:
            pass

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token.isdigit():
            return int(token)

    return None


def get_difficulty_limit(time_available):
    if time_available == "1-3":
        return 2
    if time_available == "5-10":
        return 4
    return 6


def _time_star_bounds(time_available):
    if time_available == "1-3":
        return {"max_stars": 2000, "min_stars": None}
    if time_available == "5-10":
        return {"max_stars": 10000, "min_stars": None}
    if time_available == "20+":
        return {"max_stars": None, "min_stars": 10000}
    return {"max_stars": None, "min_stars": None}


def _topic_modifier(topic_names):
    if not topic_names:
        return 2
    modifiers = []
    for name in topic_names:
        lowered = (name or "").lower()
        if "good first issue" in lowered:
            modifiers.append(-2)
        elif "documentation" in lowered:
            modifiers.append(-1)
        elif "bug" in lowered:
            modifiers.append(1)
        elif "refactor" in lowered:
            modifiers.append(3)
        else:
            modifiers.append(2)
    return min(modifiers) if modifiers else 2


def _compute_difficulty_score(repo, topic_names):
    stars = repo.stars or 0
    if stars < 1000:
        stars_score = 1
    elif stars < 10000:
        stars_score = 2
    else:
        stars_score = 3
    return stars_score + _topic_modifier(topic_names)


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


@api_bp.route("/saved-repos", methods=["GET"])
@api_bp.route("/saved-projects", methods=["GET"])
def get_saved_projects():
    from models import Repository, SavedRepository

    try:
        user_id = _extract_user_id_from_request()
        if user_id is None:
            return jsonify({
                "count": 0,
                "saved_projects": [],
                "error": "Missing authenticated user context.",
            }), 401

        rows = (
            db.session.query(
                Repository.repo_id,
                Repository.full_name,
                Repository.description,
                Repository.owner,
                Repository.language,
                Repository.stars,
                Repository.forks,
                Repository.html_url,
                SavedRepository.saved_at,
            )
            .join(SavedRepository, SavedRepository.repo_id == Repository.repo_id)
            .filter(SavedRepository.user_id == user_id)
            .order_by(SavedRepository.saved_at.desc())
            .limit(50)
            .all()
        )

        saved_projects = [
            {
                "user_id": user_id,
                "repo_id": row.repo_id,
                "full_name": row.full_name,
                "description": row.description,
                "owner": row.owner,
                "language": row.language,
                "stars": row.stars,
                "forks": row.forks,
                "html_url": row.html_url,
                "saved_at": row.saved_at.isoformat() if row.saved_at else None,
            }
            for row in rows
        ]

        return jsonify({
            "count": len(rows),
            "saved_projects": saved_projects,
            "saved_repositories": saved_projects,
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
    from models import RepoTopic, Repository, RepositoryTopic

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
    time_available = _get_field("timeAvailable")

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

    candidate_limit = 800
    q = Repository.query

    # STRUCTURED FILTERS FIRST (index-friendly)
    if language:
        q = q.filter(Repository.language.ilike(language))

    effective_min_stars = stars_gte if stars_gte is not None else 0
    time_bounds = _time_star_bounds(time_available)
    if time_bounds["min_stars"] is not None:
        effective_min_stars = max(effective_min_stars, time_bounds["min_stars"])
    q = q.filter(Repository.stars >= effective_min_stars)
    if time_bounds["max_stars"] is not None:
        q = q.filter(Repository.stars <= time_bounds["max_stars"])

    if sort == "stars":
        q = q.order_by(Repository.stars.desc())
    else:
        q = q.order_by(Repository.stars.desc())

    candidates = q.limit(candidate_limit).all()
    if not candidates:
        return jsonify({
            "count": 0,
            "time_available": time_available or None,
            "mode": "keyword" if query else "filtered",
            "results": [],
        })

    candidate_ids = [repo.repo_id for repo in candidates]

    # TOPIC MATCH ONLY WITHIN CANDIDATE WINDOW
    if topic:
        topic_rows = (
            db.session.query(RepositoryTopic.repo_id)
            .join(RepoTopic, RepoTopic.topic_id == RepositoryTopic.topic_id)
            .filter(
                RepositoryTopic.repo_id.in_(candidate_ids),
                RepoTopic.name.ilike(f"%{topic}%"),
            )
            .all()
        )
        matched_ids = {row[0] for row in topic_rows}
        candidates = [repo for repo in candidates if repo.repo_id in matched_ids]
        candidate_ids = [repo.repo_id for repo in candidates]

    # KEYWORD MATCH ON SMALL IN-MEMORY SET
    if query and candidates:
        lowered_query = query.lower()
        candidates = [
            repo
            for repo in candidates
            if lowered_query in (repo.full_name or "").lower()
            or lowered_query in (repo.description or "").lower()
        ]
        candidate_ids = [repo.repo_id for repo in candidates]

    topics_map = _topics_by_repo_id(candidate_ids)

    scored = []
    for repo in candidates:
        score = _compute_difficulty_score(repo, topics_map.get(repo.repo_id, []))
        scored.append((repo, score))

    if time_available:
        difficulty_limit = get_difficulty_limit(time_available)
        scored = [(repo, score) for repo, score in scored if score <= difficulty_limit]

    scored.sort(key=lambda item: (item[1], -(item[0].stars or 0)))
    rows = scored[:limit]
    repositories = [repo for repo, _ in rows]

    return jsonify({
        "count": len(repositories),
        "time_available": time_available or None,
        "mode": "keyword" if query else "filtered",
        "results": [
            _serialize_repository(
                repo,
                topics_map,
                difficulty_score=float(score) if score is not None else None,
            )
            for repo, score in rows
        ]
    })
