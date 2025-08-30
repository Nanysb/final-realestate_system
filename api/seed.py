# api/seed.py
from app import create_app
from models import db, Company, Project, Unit

def run_seed():
    app = create_app()
    
    with app.app_context():
        # ---------------- شركة ----------------
        company_slug = "Abu Zahra Developments"
        company_name = "Abu Zahra Developments"

        company = Company.query.filter_by(slug=company_slug).first()
        if not company:
            company = Company(slug=company_slug, name=company_name)
            db.session.add(company)
            db.session.commit()
            print(f"Company '{company_name}' added.")
        else:
            print(f"Company '{company_name}' already exists.")

        # ---------------- مشروع ----------------
        project_slug = "diva-1"
        project_title = "Diva 1"
        project_location = "New Cairo"
        project_description = "Luxury project"

        project = Project.query.filter_by(slug=project_slug, company_id=company.id).first()
        if not project:
            project = Project(
                company_id=company.id,
                slug=project_slug,
                title=project_title,
                location=project_location,
                description=project_description
            )
            db.session.add(project)
            db.session.commit()
            print(f"Project '{project_title}' added.")
        else:
            print(f"Project '{project_title}' already exists.")

        # ---------------- وحدات ----------------
        units_data = [
            {"code": "A-101", "sqm": 100, "price_per_sqm": 20000, "floor": "1"},
            {"code": "A-102", "sqm": 120, "price_per_sqm": 19500, "floor": "2"},
            {"code": "B-303", "sqm": 150, "price_per_sqm": 21000, "floor": "3"},
        ]

        existing_unit_codes = [u.code for u in Unit.query.filter_by(project_id=project.id).all()]
        new_units = []

        for udata in units_data:
            if udata["code"] not in existing_unit_codes:
                unit = Unit(
                    project_id=project.id,
                    code=udata["code"],
                    sqm=udata["sqm"],
                    price_per_sqm=udata["price_per_sqm"],
                    floor=udata["floor"]
                )
                new_units.append(unit)

        if new_units:
            db.session.add_all(new_units)
            db.session.commit()
            print(f"{len(new_units)} units added.")
        else:
            print("All units already exist.")

        print("✅ Seed done successfully!")

if __name__ == "__main__":
    run_seed()