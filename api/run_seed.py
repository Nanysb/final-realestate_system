# api/test_seed.py
from app import create_app
from models import db, Company, Project, Unit

# أنشئ التطبيق
app = create_app()

with app.app_context():
    print("🔹 جاري إنشاء الجداول...")
    db.create_all()
    print("✅ تم إنشاء الجداول")
    
    # تحقق أولاً إذا الشركة موجودة
    company = Company.query.filter_by(slug="abu-zahra").first()
    if company:
        print("⚠️  الشركة موجودة بالفعل:", company.name)
    else:
        print("🔹 جاري إضافة الشركة...")
        company = Company(slug="abu-zahra", name="Abu Zahra Developments")
        db.session.add(company)
        db.session.commit()
        print("✅ تم إضافة الشركة: Abu Zahra Developments (ID:", company.id, ")")

    # تحقق أولاً إذا المشروع موجود
    project = Project.query.filter_by(slug="diva-1").first()
    if project:
        print("⚠️  المشروع موجود بالفعل:", project.title)
    else:
        print("🔹 جاري إضافة المشروع...")
        project = Project(
            company_id=company.id,
            slug="diva-1", 
            title="Diva 1",
            location="New Cairo",
            description="Luxury project in New Cairo"
        )
        db.session.add(project)
        db.session.commit()
        print("✅ تم إضافة المشروع: Diva 1 (ID:", project.id, ")")

    # تحقق من الوحدات
    existing_units = Unit.query.filter_by(project_id=project.id).all()
    if existing_units:
        print("⚠️  يوجد", len(existing_units), "وحدات بالفعل")
    else:
        print("🔹 جاري إضافة الوحدات...")
        units = [
            Unit(project_id=project.id, code="A-101", sqm=100, price_per_sqm=20000, floor="1"),
            Unit(project_id=project.id, code="A-102", sqm=120, price_per_sqm=19500, floor="2"), 
            Unit(project_id=project.id, code="B-303", sqm=150, price_per_sqm=21000, floor="3")
        ]
        
        for unit in units:
            db.session.add(unit)
        
        db.session.commit()
        print("✅ تم إضافة 3 وحدات")
    
    # التحقق النهائي من البيانات
    print("\n🔍 التحقق النهائي من البيانات:")
    print("Companies", Company.query.count())
    print("Projects", Project.query.count()) 
    print("Units", Unit.query.count())
    
    print("🎉 done !")