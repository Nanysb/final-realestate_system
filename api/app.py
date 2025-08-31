# 1. api/app.py - بعد التعديلات
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException

from models import db, User, Company, Project, Unit
from utils import paginate_query
from auth import auth_bp

load_dotenv()

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXT

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({"ok": False, "error": "Token missing or invalid", "detail": str(e)}), 401
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"ok": False, "error": "Admins only"}), 403
        return fn(*args, **kwargs)
    return wrapper

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    CORS(app, 
         origins=["http://localhost:3000", "http://127.0.0.1:3000"],
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "Content-Disposition"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])

    # ---------- Config ----------
    instance_path = Path(app.instance_path)
    os.makedirs(instance_path, exist_ok=True)

    db_url = os.getenv("DATABASE_URL", f"sqlite:///{instance_path / 'realestate.db'}")
    jwt_secret = os.getenv("JWT_SECRET_KEY", "change-this-secret")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = jwt_secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 604800

    uploads = instance_path / "uploads"
    os.makedirs(uploads, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(uploads)

    # ---------- Logging ----------
    logs_dir = Path.cwd() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(logs_dir / "api.log", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Starting API app")

    # ---------- Extensions ----------
    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    # ---------- Error handlers ----------
    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return jsonify({"ok": False, "error": e.name, "message": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.exception("Unhandled exception")
        return jsonify({"ok": False, "error": "Internal Server Error", "message": str(e)}), 500

    # ---------- Blueprints ----------
    app.register_blueprint(auth_bp)

    # ---------- Helpers ----------
    def save_uploaded_files(files_list):
        saved_files = []
        for f in files_list:
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                
                # تأكد من وجود المجلد
                os.makedirs(os.path.dirname(target), exist_ok=True)
                
                base, ext = os.path.splitext(filename)
                idx = 1
                while os.path.exists(target):
                    filename = f"{base}_{idx}{ext}"
                    target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    idx += 1
                
                f.save(target)
                saved_files.append(filename)
                app.logger.info(f"Saved file: {filename}")
        return saved_files

    # ---------- Public Endpoints ----------
    @app.route("/")
    def home():
        return jsonify({"message": "Real Estate API is running radooo"})

    @app.route("/api/health")   
    def health():
        return jsonify({"ok": True, "status": "API running"})

    # ---------- Companies ----------
    @app.route("/api/companies", methods=["GET"])
    def get_companies():
        companies = Company.query.all()
        res = [c.to_dict() for c in companies]
        return jsonify({"ok": True, "data": res})

    @app.route("/api/companies/<string:slug>", methods=["GET"])
    def get_company_by_slug(slug):
        company = Company.query.filter_by(slug=slug).first_or_404()
        return jsonify({"ok": True, "data": company.to_dict()})

    @app.route("/api/companies", methods=["POST"])
    @admin_required
    def create_company():
        data = request.get_json() or {}
        slug = data.get("slug")
        name = data.get("name")
        if not slug or not name:
            return jsonify({"ok": False, "error": "slug/name required"}), 400
        if Company.query.filter_by(slug=slug).first():
            return jsonify({"ok": False, "error": "slug exists"}), 409
        
        c = Company(
            slug=slug, 
            name=name,
            logo=data.get("logo"),
            description=data.get("description"),
            contact_info=json.dumps(data.get("contact_info", {})) if data.get("contact_info") else None
        )
        db.session.add(c)
        db.session.commit()
        app.logger.info(f"Company created: {slug}")
        return jsonify({"ok": True, "data": c.to_dict()}), 201

    @app.route("/api/companies/<int:cid>", methods=["PUT"])
    @admin_required
    def update_company(cid):
        c = Company.query.get_or_404(cid)
        data = request.get_json() or {}
        
        if "slug" in data:
            if Company.query.filter(Company.slug == data["slug"], Company.id != cid).first():
                return jsonify({"ok": False, "error": "slug exists"}), 409
            c.slug = data["slug"]
        
        if "name" in data:
            c.name = data["name"]
        
        if "logo" in data:
            c.logo = data["logo"]
        
        if "description" in data:
            c.description = data["description"]
        
        if "contact_info" in data:
            c.contact_info = json.dumps(data["contact_info"]) if data["contact_info"] else None
        
        db.session.commit()
        app.logger.info(f"Company updated: {c.slug}")
        return jsonify({"ok": True, "data": c.to_dict()})

    @app.route("/api/companies/<int:cid>", methods=["DELETE"])
    @admin_required
    def delete_company(cid):
        c = Company.query.get_or_404(cid)
        db.session.delete(c)
        db.session.commit()
        app.logger.info(f"Company deleted: {cid}")
        return jsonify({"ok": True, "message": "Company deleted successfully"})

    # ---------- Projects ----------
    @app.route("/api/projects", methods=["GET"])
    def get_projects():
        company_slug = request.args.get("company_slug")
        status = request.args.get("status")
        
        q = Project.query
        if company_slug:
            comp = Company.query.filter_by(slug=company_slug).first()
            if not comp:
                return jsonify({"ok": False, "error": "Company not found"}), 404
            q = q.filter_by(company_id=comp.id)
        
        if status:
            q = q.filter_by(status=status)
        
        items = q.order_by(Project.order.asc().nullslast(), Project.created_at.desc()).all()
        res = [p.to_dict() for p in items]
        
        for project in res:
            project["images"] = [url_for("uploaded_file", filename=fn, _external=True) 
                                for fn in project["images"]]
        
        return jsonify({"ok": True, "data": res})

    @app.route("/api/projects/<int:pid>", methods=["GET"])
    def get_project(pid):
        project = Project.query.get_or_404(pid)
        data = project.to_dict()
        data["images"] = [url_for("uploaded_file", filename=fn, _external=True) 
                         for fn in data["images"]]
        return jsonify({"ok": True, "data": data})

    @app.route("/api/projects", methods=["POST"])
    @admin_required
    def create_project():
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            data = request.form.to_dict()
            for field in ["features"]:
                if field in data and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except json.JSONDecodeError:
                        pass
        else:
            data = request.get_json() or {}

        company_slug = data.get("company_slug")
        comp = Company.query.filter_by(slug=company_slug).first()
        if not comp:
            return jsonify({"ok": False, "error": "Company not found"}), 404

        slug = data.get("slug") or ""
        title = data.get("title") or ""
        if not slug or not title:
            return jsonify({"ok": False, "error": "slug/title required"}), 400

        p = Project(
            company_id=comp.id,
            slug=slug,
            title=title,
            location=data.get("location"),
            description=data.get("description"),
            features=json.dumps(data.get("features", [])),
            status=data.get("status", "active"),
            order=data.get("order", 0)
        )
        
        db.session.add(p)
        db.session.commit()

        saved_files = []
        if request.files:
            files = request.files.getlist("images")
            saved_files = save_uploaded_files(files)
            
            if saved_files:
                existing_images = p.get_images()
                existing_images.extend(saved_files)
                p.images = json.dumps(existing_images)
                db.session.commit()

        app.logger.info(f"Project created: {slug}")
        return jsonify({"ok": True, "data": p.to_dict()}), 201

    @app.route("/api/projects/<int:pid>", methods=["PUT"])
    @admin_required
    def update_project(pid):
        p = Project.query.get_or_404(pid)
        
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            data = request.form.to_dict()
            for field in ["features"]:
                if field in data and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except json.JSONDecodeError:
                        pass
        else:
            data = request.get_json() or {}
            
        if "slug" in data:
            if Project.query.filter(Project.slug == data["slug"], Project.id != pid).first():
                return jsonify({"ok": False, "error": "slug exists"}), 409
            p.slug = data["slug"]
            
        for field in ["title", "location", "description", "status", "order"]:
            if field in data:
                setattr(p, field, data[field])
                
        if "features" in data:
            p.features = json.dumps(data["features"])
                
        db.session.commit()
        app.logger.info(f"Project updated: {p.slug}")
        return jsonify({"ok": True, "data": p.to_dict()})

    @app.route("/api/projects/<int:pid>", methods=["DELETE"])
    @admin_required
    def delete_project(pid):
        p = Project.query.get_or_404(pid)
        db.session.delete(p)
        db.session.commit()
        app.logger.info(f"Project deleted: {pid}")
        return jsonify({"ok": True, "message": "Project deleted successfully"})

    @app.route("/api/projects/<int:pid>/upload", methods=["POST"])
    @admin_required
    def upload_project_files(pid):
        p = Project.query.get_or_404(pid)
        if "images" not in request.files:
            return jsonify({"ok": False, "error": "No images field"}), 400

        files = request.files.getlist("images")
        saved_files = save_uploaded_files(files)

        if saved_files:
            existing_images = p.get_images()
            existing_images.extend(saved_files)
            p.images = json.dumps(existing_images)
            db.session.commit()

        app.logger.info(f"Uploaded {len(saved_files)} files to project {pid}")
        return jsonify({"ok": True, "data": saved_files})

    # ---------- Upload Endpoint ----------
    @app.route("/api/upload", methods=["POST"])
    @admin_required
    def upload_file():
        if 'file' not in request.files:
            return jsonify({"ok": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"ok": False, "error": "No file selected"}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            
            base, ext = os.path.splitext(filename)
            idx = 1
            while os.path.exists(target):
                filename = f"{base}_{idx}{ext}"
                target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                idx += 1
            
            file.save(target)
            app.logger.info(f"File uploaded: {filename}")
            return jsonify({"ok": True, "filename": filename})
        
        return jsonify({"ok": False, "error": "File type not allowed"}), 400

    # ---------- Units ----------
    @app.route("/api/units", methods=["GET"])
    def list_units():
        project_id = request.args.get("project_id", type=int)
        min_sqm = request.args.get("min_sqm", type=float)
        max_price = request.args.get("max_price", type=int)
        floor = request.args.get("floor")
        status = request.args.get("status")
        bedrooms = request.args.get("bedrooms", type=int)
        bathrooms = request.args.get("bathrooms", type=int)

        q = Unit.query
        if project_id:
            q = q.filter_by(project_id=project_id)
        if min_sqm:
            q = q.filter(Unit.sqm >= min_sqm)
        if status:
            q = q.filter_by(status=status)
        if bedrooms:
            q = q.filter(Unit.bedrooms == bedrooms)
        if bathrooms:
            q = q.filter(Unit.bathrooms == bathrooms)

        items, page, limit = paginate_query(q.order_by(Unit.created_at.desc()))
        units = [u.to_dict() for u in items]

        if max_price:
            units = [u for u in units if u.get("total_price", float("inf")) <= max_price]
        if floor:
            units = [u for u in units if str(u.get("floor")) == str(floor)]

        for unit in units:
            unit["images"] = [url_for("uploaded_file", filename=fn, _external=True) 
                             for fn in unit["images"]]
            if unit["floor_plan"]:
                unit["floor_plan"] = url_for("uploaded_file", filename=unit["floor_plan"], _external=True)

        return jsonify({
            "ok": True, 
            "data": units,
            "pagination": {"page": page, "limit": limit, "total": len(units)}
        })

    @app.route("/api/units/<int:uid>", methods=["GET"])
    def get_unit(uid):
        u = Unit.query.get_or_404(uid)
        data = u.to_dict()
        data["images"] = [url_for("uploaded_file", filename=fn, _external=True) 
                         for fn in data["images"]]
        if data["floor_plan"]:
            data["floor_plan"] = url_for("uploaded_file", filename=data["floor_plan"], _external=True)
        return jsonify({"ok": True, "data": data})

    @app.route("/api/units", methods=["POST"])
    @admin_required
    def create_unit():
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            data = request.form.to_dict()
            for field in ["amenities", "metadata"]:
                if field in data and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except json.JSONDecodeError:
                        pass
        else:
            data = request.get_json() or {}
            
        project_id = data.get("project_id")
        code = data.get("code")
        sqm = data.get("sqm")
        price_per_sqm = data.get("price_per_sqm")
        floor = data.get("floor")

        if not all([project_id, code, sqm, price_per_sqm, floor]):
            return jsonify({"ok": False, "error": "project_id, code, sqm, price_per_sqm, floor required"}), 400

        _ = Project.query.get_or_404(project_id)
        u = Unit(
            project_id=project_id,
            code=str(code),
            sqm=float(sqm),
            price_per_sqm=int(price_per_sqm),
            floor=str(floor),
            title=data.get("title"),
            bedrooms=data.get("bedrooms", 0),
            bathrooms=data.get("bathrooms", 0),
            amenities=json.dumps(data.get("amenities", [])),
            unit_metadata=json.dumps(data.get("metadata", {})),
            status=data.get("status", "available")
        )
        
        db.session.add(u)
        db.session.commit()
        
        saved_files = []
        if request.files:
            files = request.files.getlist("images")
            saved_files = save_uploaded_files(files)
            
            if saved_files:
                u.images = json.dumps(saved_files)
                db.session.commit()
                
        if "floor_plan" in request.files:
            floor_plan_file = request.files["floor_plan"]
            if floor_plan_file and allowed_file(floor_plan_file.filename):
                filename = secure_filename(floor_plan_file.filename)
                target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                base, ext = os.path.splitext(filename)
                idx = 1
                while os.path.exists(target):
                    filename = f"{base}_{idx}{ext}"
                    target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    idx += 1
                floor_plan_file.save(target)
                u.floor_plan = filename
                db.session.commit()

        app.logger.info(f"Unit created: {code}")
        return jsonify({"ok": True, "data": u.to_dict()}), 201

    @app.route("/api/units/<int:uid>", methods=["PUT"])
    @admin_required
    def update_unit(uid):
        u = Unit.query.get_or_404(uid)
        
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            data = request.form.to_dict()
            for field in ["amenities", "metadata"]:
                if field in data and data[field]:
                    try:
                        data[field] = json.loads(data[field])
                    except json.JSONDecodeError:
                        pass
        else:
            data = request.get_json() or {}
            
        for field in ["code", "title", "floor", "status"]:
            if field in data and data[field] is not None:
                setattr(u, field, str(data[field]))
                
        if "sqm" in data and data["sqm"] is not None:
            u.sqm = float(data["sqm"])
            
        if "price_per_sqm" in data and data["price_per_sqm"] is not None:
            u.price_per_sqm = int(data["price_per_sqm"])
            
        if "bedrooms" in data and data["bedrooms"] is not None:
            u.bedrooms = int(data["bedrooms"])
            
        if "bathrooms" in data and data["bathrooms"] is not None:
            u.bathrooms = int(data["bathrooms"])
            
        if "amenities" in data:
            u.amenities = json.dumps(data["amenities"])
            
        if "metadata" in data:
            u.unit_metadata = json.dumps(data["metadata"])
            
        if "images" in request.files:
            files = request.files.getlist("images")
            saved_files = save_uploaded_files(files)
            
            if saved_files:
                existing_images = u.get_images()
                existing_images.extend(saved_files)
                u.images = json.dumps(existing_images)
                
        if "floor_plan" in request.files:
            floor_plan_file = request.files["floor_plan"]
            if floor_plan_file and allowed_file(floor_plan_file.filename):
                filename = secure_filename(floor_plan_file.filename)
                target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                base, ext = os.path.splitext(filename)
                idx = 1
                while os.path.exists(target):
                    filename = f"{base}_{idx}{ext}"
                    target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    idx += 1
                floor_plan_file.save(target)
                u.floor_plan = filename
        
        db.session.commit()
        app.logger.info(f"Unit updated: {u.code}")
        return jsonify({"ok": True, "data": u.to_dict()})

    @app.route("/api/units/<int:uid>", methods=["DELETE"])
    @admin_required
    def delete_unit(uid):
        u = Unit.query.get_or_404(uid)
        db.session.delete(u)
        db.session.commit()
        app.logger.info(f"Unit deleted: {uid}")
        return jsonify({"ok": True, "message": "Unit deleted successfully"})

    @app.route("/api/units/<int:uid>/upload", methods=["POST"])
    @admin_required
    def upload_unit_files(uid):
        u = Unit.query.get_or_404(uid)
        if "images" not in request.files and "floor_plan" not in request.files:
            return jsonify({"ok": False, "error": "No files provided"}), 400

        saved_files = []
        if "images" in request.files:
            files = request.files.getlist("images")
            saved_files = save_uploaded_files(files)
            
            if saved_files:
                existing_images = u.get_images()
                existing_images.extend(saved_files)
                u.images = json.dumps(existing_images)
                
        if "floor_plan" in request.files:
            floor_plan_file = request.files["floor_plan"]
            if floor_plan_file and allowed_file(floor_plan_file.filename):
                filename = secure_filename(floor_plan_file.filename)
                target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                base, ext = os.path.splitext(filename)
                idx = 1
                while os.path.exists(target):
                    filename = f"{base}_{idx}{ext}"
                    target = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    idx += 1
                floor_plan_file.save(target)
                u.floor_plan = filename
                saved_files.append(filename)

        db.session.commit()
        app.logger.info(f"Uploaded {len(saved_files)} files to unit {uid}")
        return jsonify({"ok": True, "data": saved_files})

    # Serve uploaded files - مع handling للأخطاء
    @app.route("/api/uploads/<path:filename>")
    def uploaded_file(filename):
        try:
            return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
        except FileNotFoundError:
            app.logger.warning(f"File not found: {filename}")
            return jsonify({"ok": False, "error": "File not found"}), 404

    # ---------- App context initialization ----------
    with app.app_context():
        db.create_all()
        admin_user = os.getenv("ADMIN_DEFAULT_USER", "admin")
        admin_pass = os.getenv("ADMIN_DEFAULT_PASS", "admin123")
        if not User.query.filter_by(username=admin_user).first():
            u = User(username=admin_user, role="admin")
            u.set_password(admin_pass)
            db.session.add(u)
            db.session.commit()
            app.logger.info("Created default admin user '%s'", admin_user)

    return app

if __name__ == "__main__":
    from waitress import serve
    app = create_app()
    serve(app, host="127.0.0.1", port=5000)