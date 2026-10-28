import json
from datetime import datetime
from backend.database.db import db


class Article(db.Model):
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    url = db.Column(db.String(2000))
    source = db.Column(db.String(200))
    article_text = db.Column(db.Text)
    summary = db.Column(db.Text)          # stored as JSON string
    key_points = db.Column(db.Text)       # stored as JSON string
    result_json = db.Column(db.Text)      # optional raw result
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to claims
    claims = db.relationship('Claim', backref='article', lazy=True, cascade="all, delete-orphan")

    def to_summary_dict(self):
        # Parse key_points safely
        try:
            kp = json.loads(self.key_points) if self.key_points else []
        except Exception:
            kp = []

        # Parse summary safely
        try:
            summ = json.loads(self.summary) if self.summary else ""
        except Exception:
            summ = self.summary or ""

        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "summary": summ,
            "key_points": kp,
            "claims_count": len(self.claims),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def to_dict(self):
        data = self.to_summary_dict()
        data["article_text"] = self.article_text
        data["claims"] = [c.to_dict() for c in self.claims]
        return data
