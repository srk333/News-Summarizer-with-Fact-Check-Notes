from backend.database.db import db

class Evidence(db.Model):
    __tablename__ = 'evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey('claims.id'), nullable=False)
    source_title = db.Column(db.String(500), nullable=True)
    source_url = db.Column(db.String(2048), nullable=True)
    source_domain = db.Column(db.String(200), nullable=True)
    evidence_text = db.Column(db.Text, nullable=False)
    source_quality = db.Column(db.String(50), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'claim_id': self.claim_id,
            'source_title': self.source_title,
            'source_url': self.source_url,
            'source_domain': self.source_domain,
            'evidence_text': self.evidence_text,
            'source_quality': self.source_quality
        }
