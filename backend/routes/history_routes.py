from flask import Blueprint, jsonify, g

from backend.database.db import db
from backend.models.article import Article
from backend.models.claim import Claim
from backend.routes.auth_routes import login_required

history_bp = Blueprint('history', __name__)


@history_bp.route('/api/history', methods=['GET'])
@login_required
def get_history():
    articles = (Article.query.filter_by(user_id=g.user.id)
                .order_by(Article.created_at.desc()).limit(100).all())
    return jsonify([{
        "id": a.id,
        "title": a.title,
        "source": a.source,
        "url": a.url,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "claims_count": Claim.query.filter_by(article_id=a.id).count(),
    } for a in articles])


@history_bp.route('/api/history/<int:article_id>', methods=['GET'])
@login_required
def get_history_item(article_id):
    article = Article.query.filter_by(id=article_id, user_id=g.user.id).first()
    if not article:
        return jsonify({"error": "Analysis not found."}), 404
    return jsonify(article.to_dict())


@history_bp.route('/api/history/<int:article_id>', methods=['DELETE'])
@login_required
def delete_history_item(article_id):
    article = Article.query.filter_by(id=article_id, user_id=g.user.id).first()
    if not article:
        return jsonify({"error": "Analysis not found."}), 404
    db.session.delete(article)
    db.session.commit()
    return jsonify({"deleted": True})