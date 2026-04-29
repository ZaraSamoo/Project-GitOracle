from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from extensions import db

api_bp = Blueprint("api_bp", __name__)


def resolve_html_url(repo):
    html_url = (repo.html_url or "").strip() if repo.html_url else ""
    if html_url.startswith("https://github.com/"):
        return html_url

    full_name = (repo.full_name or "").strip() if repo.full_name else ""
    if "/" in full_name:
        return f"https://github.com/{full_name}"

    return None


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
    return jsonify(
        {
            "count": len(repositories),
            "repositories": [
                {
                    "repo_id": repo.repo_id,
                    "github_id": repo.github_id,
                    "owner": repo.owner,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "stars": repo.stars,
                    "forks": repo.forks,
                    "language": repo.language,
                    "html_url": repo.html_url,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                }
                for repo in repositories
            ],
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

    saved_projects = (
        db.session.query(Repository, SavedRepository)
        .join(SavedRepository, SavedRepository.repo_id == Repository.repo_id)
        .filter(SavedRepository.user_id == 1)
        .order_by(SavedRepository.saved_at.desc())
        .all()
    )

    return jsonify(
        {
            "count": len(saved_projects),
            "saved_projects": [
                {
                    "user_id": saved.user_id,
                    "repo_id": repo.repo_id,
                    "full_name": repo.full_name,
                    "owner": repo.owner,
                    "name": repo.name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stars,
                    "forks": repo.forks,
                    "html_url": repo.html_url,
                    "saved_at": saved.saved_at.isoformat() if saved.saved_at else None,
                }
                for repo, saved in saved_projects
            ],
        }
    )


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


@api_bp.route("/search", methods=["GET"])
def search_repositories():
    from models import Repository

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"count": 0, "results": []})

    pattern = f"%{query}%"
    repositories = (
        Repository.query.filter(
            or_(
                Repository.full_name.ilike(pattern),
                Repository.description.ilike(pattern),
            )
        )
        .order_by(Repository.stars.desc())
        .limit(20)
        .all()
    )

    return jsonify(
        {
            "count": len(repositories),
            "results": [
                {
                    "repo_id": repo.repo_id,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "stars": repo.stars,
                    "language": repo.language,
                    "html_url": resolve_html_url(repo),
                }
                for repo in repositories
            ],
        }
    )
