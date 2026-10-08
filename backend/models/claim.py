from backend.database.db import db

class Claim(db.Model):
    __tablename__ = 'claims'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    claim_text = db.Column(db.Text, nullable=False)
    claim_type = db.Column(db.String(100), nullable=True)
    importance = db.Column(db.String(50), nullable=True)
    verdict = db.Column(db.String(50), nullable=True)
    fact_check_note = db.Column(db.Text, nullable=True)
    
    evidence = db.relationship('Evidence', backref='claim', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'article_id': self.article_id,
            'claim_text': self.claim_text,
            'claim_type': self.claim_type,
            'importance': self.importance,
            'verdict': self.verdict,
            'fact_check_note': self.fact_check_note,
            'evidence': [e.to_dict() for e in self.evidence]
        }
