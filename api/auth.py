# 2. api/auth.py - الإصدار المصحح
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token,
    get_jwt_identity, 
    jwt_required, 
    get_jwt,
    JWTManager
)
from models import db, User
from datetime import timedelta
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.post("/register")
@jwt_required()
def register():
    try:
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
        
        return jsonify({
            "ok": True, 
            "id": u.id, 
            "username": u.username, 
            "role": u.role
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@auth_bp.post("/login")
def login():
    try:
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"ok": False, "error": "Username and password required"}), 400

        u = User.query.filter_by(username=username).first()
        if not u or not u.check_password(password):
            return jsonify({"ok": False, "error": "Invalid credentials"}), 401

        access_token = create_access_token(
            identity=str(u.id), 
            additional_claims={
                "role": u.role, 
                "username": u.username,
                "type": "access"
            }
        )
        
        refresh_token = create_refresh_token(
            identity=str(u.id),
            additional_claims={
                "role": u.role, 
                "username": u.username,
                "type": "refresh"
            }
        )
        
        return jsonify({
            "ok": True, 
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": u.id,
                "username": u.username,
                "role": u.role
            }
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@auth_bp.get("/verify")
@jwt_required()
def verify_token():
    try:
        claims = get_jwt()
        current_user = get_jwt_identity()
        
        if claims.get("type") != "access":
            return jsonify({"ok": False, "error": "Invalid token type"}), 401
            
        return jsonify({
            "ok": True, 
            "user": {
                "id": current_user,
                "username": claims.get("username"),
                "role": claims.get("role")
            }
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 401

@auth_bp.post('/refresh')
@jwt_required(refresh=True)
def refresh():
    try:
        claims = get_jwt()
        current_user = get_jwt_identity()
        
        if claims.get("type") != "refresh":
            return jsonify({"ok": False, "error": "Invalid refresh token"}), 422
            
        new_access_token = create_access_token(
            identity=current_user,
            additional_claims={
                "role": claims.get("role", "user"),
                "username": claims.get("username", ""),
                "type": "access"
            }
        )
        
        return jsonify({
            "ok": True, 
            "access_token": new_access_token
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 401

@auth_bp.post('/logout')
@jwt_required()
def logout():
    try:
        return jsonify({
            "ok": True, 
            "message": "Logged out successfully"
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@auth_bp.post('/validate')
def validate_token():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"ok": False, "error": "Token missing"}), 401
            
        return jsonify({"ok": True, "message": "Token is valid"})
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 401