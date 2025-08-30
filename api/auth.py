from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
from models import db, User
from os import getenv

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.post("/register")
@jwt_required()
def register():
    # مسموح فقط للأدمن
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"ok": False, "error": "Admins only"}), 403

    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not password:
        return jsonify({"ok": False, "error": "username/password required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"ok": False, "error": "User exists"}), 409

    u = User(username=username, role=role)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return jsonify({"ok": True, "id": u.id, "username": u.username, "role": u.role})

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    u = User.query.filter_by(username=username).first()
    if not u or not u.check_password(password):
        return jsonify({"ok": False, "error": "Invalid credentials"}), 401

    token = create_access_token(identity=u.id, additional_claims={"role": u.role, "username": u.username})
    return jsonify({"ok": True, "access_token": token})

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user)
        return jsonify({"ok": True, "access_token": new_token})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 401