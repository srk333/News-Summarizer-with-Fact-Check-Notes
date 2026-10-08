from backend.app import app
from backend.database.db import db
from backend.models.article import Article

with app.app_context():
    db.create_all()
    # add a dummy article
    if not Article.query.first():
        new_article = Article(title="Test DB Setup", article_text="This is a test.")
        db.session.add(new_article)
        db.session.commit()
        print("Database initialized and test article added.")
    else:
        print("Database already contains data.")
