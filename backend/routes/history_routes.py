from flask import Blueprint, jsonify
from backend.models.article import Article
from backend.database.db import db

history_bp = Blueprint('history', __name__)

@history_bp.route('/api/history', methods=['GET'])
def get_history():
    try:
        articles = Article.query.order_by(Article.created_at.desc()).all()
        # Return basic info to list
        history = []
        for a in articles:
            history.append({
                'id': a.id,
                'title': a.title,
                'source': a.source,
                'created_at': a.created_at.isoformat(),
                'claims_count': len(a.claims)
            })
        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@history_bp.route('/api/history/<int:article_id>', methods=['GET'])
def get_article(article_id):
    try:
        article = Article.query.get_or_404(article_id)
        return jsonify(article.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@history_bp.route('/api/history/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    try:
        article = Article.query.get_or_404(article_id)
        db.session.delete(article)
        db.session.commit()
        return jsonify({"message": "Deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
