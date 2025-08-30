from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# ---------------------- User ----------------------
class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")  # user | admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat()
        }

# ---------------------- Company ----------------------
class Company(db.Model):
    __tablename__ = "companies"
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, index=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    logo = db.Column(db.String(255))  # شعار الشركة
    description = db.Column(db.Text)   # وصف الشركة
    contact_info = db.Column(db.Text)  # معلومات الاتصال (JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    projects = db.relationship("Project", backref="company", cascade="all, delete-orphan")
    
    def get_contact_info(self):
        try:
            return json.loads(self.contact_info or "{}")
        except:
            return {}
    
    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "logo": self.logo,
            "description": self.description,
            "contact_info": self.get_contact_info(),
            "created_at": self.created_at.isoformat()
        }

# ---------------------- Project ----------------------
class Project(db.Model):
    __tablename__ = "projects"
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    slug = db.Column(db.String(80), index=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150))
    description = db.Column(db.Text)
    images = db.Column(db.Text)  # قائمة صور المشروع (JSON)
    features = db.Column(db.Text)  # مميزات المشروع (JSON)
    status = db.Column(db.String(20), default="active")  # active | completed | upcoming
    order = db.Column(db.Integer, default=0)  # للترتيب في العرض
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    units = db.relationship("Unit", backref="project", cascade="all, delete-orphan")
    
    def get_images(self):
        try:
            return json.loads(self.images or "[]")
        except:
            return []
    
    def get_features(self):
        try:
            return json.loads(self.features or "[]")
        except:
            return []
    
    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "slug": self.slug,
            "title": self.title,
            "location": self.location,
            "description": self.description,
            "images": self.get_images(),
            "features": self.get_features(),
            "status": self.status,
            "order": self.order,
            "created_at": self.created_at.isoformat(),
            "units_count": len(self.units)
        }

# ---------------------- Unit ----------------------
class Unit(db.Model):
    __tablename__ = "units"
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    code = db.Column(db.String(80), index=True, nullable=False)
    title = db.Column(db.String(150))  # عنوان الوحدة (شقة، فيلا)
    sqm = db.Column(db.Float, nullable=False)
    price_per_sqm = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.String(20), nullable=False)
    bedrooms = db.Column(db.Integer, default=0)  # عدد الغرف
    bathrooms = db.Column(db.Integer, default=0)  # عدد الحمامات
    images = db.Column(db.Text)  # صور الوحدة (JSON)
    floor_plan = db.Column(db.String(255))  # مخطط الوحدة
    amenities = db.Column(db.Text)  # المرافق (JSON)
    status = db.Column(db.String(20), default="available")  # available | sold | reserved
    unit_metadata = db.Column(db.Text)  # غيرنا من metadata إلى unit_metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # أضف هذه الدوال الناقصة:
    def get_images(self):
        try:
            return json.loads(self.images or "[]")
        except:
            return []

    def get_amenities(self):
        try:
            return json.loads(self.amenities or "[]")
        except:
            return []

    def get_metadata(self):
        try:
            return json.loads(self.unit_metadata or "{}")
        except:
            return {}

    @property
    def total_price(self):
        return int(self.sqm * self.price_per_sqm)
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "code": self.code,
            "title": self.title,
            "sqm": self.sqm,
            "price_per_sqm": self.price_per_sqm,
            "floor": self.floor,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "images": self.get_images(),  # هذه تحتاج get_images()
            "floor_plan": self.floor_plan,
            "amenities": self.get_amenities(),  # هذه تحتاج get_amenities()
            "status": self.status,
            "total_price": self.total_price,
            "metadata": self.get_metadata(),  # هذه تحتاج get_metadata()
            "created_at": self.created_at.isoformat()
        }