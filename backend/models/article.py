from datetime import datetime
from backend.database.db import db
import json

class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=True)
    title = db.Column(db.String(500), nullable=True)
    source = db.Column(db.String(200), nullable=True)
    article_text = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    key_points = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    claims = db.relationship('Claim', backref='article', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        try:
            summary_val = json.loads(self.summary) if self.summary else None
        except:
            summary_val = self.summary
        try:
            key_points_val = json.loads(self.key_points) if self.key_points else []
        except:
            key_points_val = []

        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'source': self.source,
            'article_text': self.article_text,
            'summary': summary_val,
            'key_points': key_points_val,
            'created_at': self.created_at.isoformat(),
            'claims': [c.to_dict() for c in self.claims]
        }
