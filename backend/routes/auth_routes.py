import re
from functools import wraps

from flask import Blueprint, request, jsonify, g, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from backend.database.db import db
from backend.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

TOKEN_MAX_AGE = 7 * 24 * 3600  # tokens last 7 days
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="newslens-auth")


def make_token(user):
    return _serializer().dumps({"uid": user.id})


def get_current_user():
    """Return the logged-in User from the Authorization header, or None."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        data = _serializer().loads(header[7:], max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return db.session.get(User, data["uid"])


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Please log in to continue."}), 401
        g.user = user
        return fn(*args, **kwargs)
    return wrapper


@auth_bp.post("/register")
def register():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"token": make_token(user), "email": user.email}), 201


@auth_bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401
    return jsonify({"token": make_token(user), "email": user.email})


@auth_bp.get("/me")
@login_required
def me():
    return jsonify({"email": g.user.email})