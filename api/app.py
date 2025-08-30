import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from dotenv import load_dotenv

from .models import db, User, Company, Project, Unit
from .utils import paginate_query
from .auth import auth_bp


load_dotenv()  # load .env

def create_app():
    app = Flask(__name__)
    CORS(app)

    db_url = os.getenv("DATABASE_URL", "sqlite:///realestate.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this")

    db.init_app(app)
    with app.app_context():
        db.create_all()
        # إنشاء أدمن ابتدائي لو مش موجود
        admin_user = os.getenv("ADMIN_DEFAULT_USER", "admin")
        admin_pass = os.getenv("ADMIN_DEFAULT_PASS", "admin123")
        if not User.query.filter_by(username=admin_user).first():
            u = User(username=admin_user, role="admin")
            u.set_password(admin_pass)
            db.session.add(u)
            db.session.commit()

    jwt = JWTManager(app)

    # Blueprints
    app.register_blueprint(auth_bp)

    # ------------------ Public Endpoints ------------------
    @app.get("/api/companies")
    def get_companies():
        companies = Company.query.all()
        return jsonify({"ok": True, "companies": [{"id": c.id, "slug": c.slug, "name": c.name} for c in companies]})

    @app.get("/api/projects")
    def get_projects():
        company_slug = request.args.get("company_slug")
        q = Project.query
        if company_slug:
            comp = Company.query.filter_by(slug=company_slug).first()
            if not comp:
                return jsonify({"ok": False, "error": "Company not found"}), 404
            q = q.filter_by(company_id=comp.id)

        items = q.order_by(Project.created_at.desc()).all()
        res = [{
            "id": p.id, "slug": p.slug, "title": p.title,
            "location": p.location, "company_id": p.company_id
        } for p in items]
        return jsonify({"ok": True, "projects": res})

    @app.get("/api/units")
    def list_units():
        project_id = request.args.get("project_id", type=int)
        min_sqm = request.args.get("min_sqm", type=float)
        max_price = request.args.get("max_price", type=int)
        floor = request.args.get("floor")

        q = Unit.query
        if project_id:
            q = q.filter_by(project_id=project_id)
        if min_sqm:
            q = q.filter(Unit.sqm >= min_sqm)
        if max_price:
            # filter using computed total_price: sqm*price_per_sqm
            # approximate with price_per_sqm <= max_price / sqm (or fetch and filter after)
            # Simpler: fetch all then filter in memory
            pass

        # paginate
        items, page, limit = paginate_query(q.order_by(Unit.created_at.desc()))
        units = [u.to_dict() for u in items]

        # if max_price provided, filter post-query to keep it simple
        if max_price:
            units = [u for u in units if u["total_price"] <= max_price]

        if floor:
            units = [u for u in units if str(u["floor"]) == str(floor)]

        return jsonify({"ok": True, "page": page, "limit": limit, "units": units})

    @app.get("/api/units/<int:unit_id>")
    def get_unit(unit_id):
        u = Unit.query.get_or_404(unit_id)
        return jsonify({"ok": True, "unit": u.to_dict()})

    # ------------------ Admin Endpoints (JWT) ------------------
    def admin_required():
        claims = get_jwt()
        if claims.get("role") != "admin":
            return False
        return True

    # Companies
    @app.post("/api/companies")
    @jwt_required()
    def create_company():
        if not admin_required():
            return jsonify({"ok": False, "error": "Admins only"}), 403
        data = request.get_json() or {}
        slug = data.get("slug")
        name = data.get("name")
        if not slug or not name:
            return jsonify({"ok": False, "error": "slug/name required"}), 400
        if Company.query.filter_by(slug=slug).first():
            return jsonify({"ok": False, "error": "slug exists"}), 409
        c = Company(slug=slug, name=name)
        db.session.add(c)
        db.session.commit()
        return jsonify({"ok": True, "company": {"id": c.id, "slug": c.slug, "name": c.name}})

    @app.put("/api/companies/<int:cid>")
    @jwt_required()
    def update_company(cid):
        if not admin_required():
            return jsonify({"ok": False, "error": "Admins only"}), 403
        c = Company.query.get_or_404(cid)
        data = request.get_json() or {}
        if "slug" in data:
            # ensure unique
            if Company.query.filter(Company.slug == data["slug"], Company.id != cid).first():
                return jsonify({"ok": False, "error": "slug exists"}), 409
            c.slug = data["slug"]
        if "name" in data:
            c.name = data["name"]
        db.session.commit()
        return jsonify({"ok": True})

    @app.delete("/api/companies/<int:cid>")
    @jwt_required()
    def delete_company(cid):
        if not admin_required():
            return jsonify({"ok": False, "error": "Admins only"}), 403
        c = Company.query.get_or_404(cid)
        db.session.delete(c)
        db.session.commit()
        return jsonify({"ok": True})

    # Projects
    @app.post("/api/projects")
    @jwt_required()
    def create_project():
        if not admin_required():
            return jsonify({"ok": False, "error": "Admins only"}), 403
        data = request.get_json() or {}
        company_slug = data.get("company_slug")
        comp = Company.query.filter_by(slug=company_slug).first()
        if not comp:
            return jsonify({"ok": False, "error": "Company not found"}), 404

        p = Project(
            company_id=comp.id,
            slug=data.get("slug", ""),
            title=data.get("title", ""),
            location=data.get("location"),
            description=data.get("description")
        )
        if not p.slug or not p.title:
            return jsonify({"ok": False, "error": "slug/title required"}), 400

        db.session.add(p)
        db.session.commit()
        return jsonify({"ok": True, "project": {
            "id": p.id, "slug": p.slug, "title": p.title, "company_id": p.company_id
        }})

    @app.put("/api/projects/<int:pid>")
    @jwt_required()
    def update_project(pid):
        if not admin_required():
            return jsonify({"ok": False, "error": "Admins only"}), 403
        p = Project.query.get_or_404(pid)
        data = request.get_json() or {}
        for k in ["slug", "title", "location", "description"]:
            if k in data:
                setattr(p, k, data[k])
        db.session.commit()
        return jsonify({"ok": True})

    @app.delete("/api/projects/<int:pid>")
    @jwt_required()
    def delete_project(pid):
        if not admin_required():
            return jsonify({"ok": False, "error": "Admins only"}), 403
        p = Project.query.get_or_404(pid)
        db.session.delete(p)
        db.session.commit()
        return jsonify({"ok": True})

    # Units
    @app.post("/api/units")
    @jwt_required()
    def create_unit():
        if not admin_required():
            return jsonify({"ok": False, "error": "Admins only"}), 403
        data = request.get_json() or {}
        project_id = data.get("project_id")
        code = data.get("code")
        sqm = data.get("sqm")
        price_per_sqm = data.get("price_per_sqm")
        floor = data.get("floor")

        if not all([project_id, code, sqm, price_per_sqm, floor]):
            return jsonify({"ok": False, "error": "project_id, code, sqm, price_per_sqm, floor required"}), 400

        # ensure project exists
        _ = Project.query.get_or_404(project_id)

        u = Unit(
            project_id=project_id,
            code=str(code),
            sqm=float(sqm),
            price_per_sqm=int(price_per_sqm),
            floor=str(floor),
            status=data.get("status", "available")
        )
        db.session.add(u)
        db.session.commit()
        return jsonify({"ok": True, "unit": u.to_dict()})

    @app.put("/api/units/<int:uid>")
    @jwt_required()
    def update_unit(uid):
        if not admin_required():
            return jsonify({"ok": False, "error": "Admins only"}), 403
        u = Unit.query.get_or_404(uid)
        data = request.get_json() or {}
        for k in ["code", "sqm", "price_per_sqm", "floor", "status"]:
            if k in data and data[k] is not None:
                if k in ["sqm"]:
                    setattr(u, k, float(data[k]))
                elif k in ["price_per_sqm"]:
                    setattr(u, k, int(data[k]))
                else:
                    setattr(u, k, str(data[k]))
        db.session.commit()
        return jsonify({"ok": True})

    @app.delete("/api/units/<int:uid>")
    @jwt_required()
    def delete_unit(uid):
        if not admin_required():
            return jsonify({"ok": False, "error": "Admins only"}), 403
        u = Unit.query.get_or_404(uid)
        db.session.delete(u)
        db.session.commit()
        return jsonify({"ok": True})

    # Health
    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "status": "API running"})

    return app

# ------------- Entrypoint -------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
