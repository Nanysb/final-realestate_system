from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ---------------------- User ----------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")  # user | admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

# ---------------------- Company ----------------------
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, index=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    projects = db.relationship("Project", backref="company", cascade="all, delete-orphan")

# ---------------------- Project ----------------------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    slug = db.Column(db.String(80), index=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    units = db.relationship("Unit", backref="project", cascade="all, delete-orphan")

# ---------------------- Unit ----------------------
class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    code = db.Column(db.String(80), index=True, nullable=False)
    sqm = db.Column(db.Float, nullable=False)
    price_per_sqm = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="available")  # available | sold | reserved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def total_price(self):
        return int(self.sqm * self.price_per_sqm)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "code": self.code,
            "sqm": self.sqm,
            "price_per_sqm": self.price_per_sqm,
            "floor": self.floor,
            "status": self.status,
            "total_price": self.total_price
        }
