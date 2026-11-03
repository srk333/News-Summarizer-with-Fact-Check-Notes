from sqlalchemy import text
from backend.app import app
from backend.database.db import db

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE articles ADD COLUMN user_id INTEGER"))
        db.session.commit()
        print("Added articles.user_id")
    except Exception as e:
        db.session.rollback()
        print("Skipped:", e)