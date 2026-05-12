import bcrypt

from .extensions import db
from .models import Medicine, User


def seed_data():
    if not Medicine.query.first():
        medicines = [
            Medicine(name="Paracetamol", quantity=100, price=5.99),
            Medicine(name="Ibuprofen", quantity=50, price=7.49),
            Medicine(name="Amoxicillin", quantity=20, price=12.99),
            Medicine(name="Cetirizine", quantity=30, price=6.49),
            Medicine(name="Vitamin C", quantity=80, price=4.99),
            Medicine(name="Omeprazole", quantity=25, price=15.99),
            Medicine(name="Azithromycin", quantity=15, price=18.99),
            Medicine(name="Metformin", quantity=40, price=9.99),
            Medicine(name="Aspirin", quantity=60, price=3.99),
            Medicine(name="Loratadine", quantity=35, price=8.49),
            Medicine(name="Lisinopril", quantity=30, price=11.99),
            Medicine(name="Atorvastatin", quantity=25, price=14.99),
            Medicine(name="Metoprolol", quantity=40, price=10.49),
            Medicine(name="Levothyroxine", quantity=50, price=9.49),
            Medicine(name="Ciprofloxacin", quantity=20, price=13.99),
            Medicine(name="Pantoprazole", quantity=30, price=16.49),
            Medicine(name="Doxycycline", quantity=15, price=17.99),
            Medicine(name="Hydrochlorothiazide", quantity=45, price=8.99),
            Medicine(name="Vitamin D", quantity=70, price=5.49),
            Medicine(name="Folic Acid", quantity=60, price=4.49),
        ]
        db.session.bulk_save_objects(medicines)

    if not User.query.filter_by(email="admin@example.com").first():
        hashed_password = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt())
        admin = User(email="admin@example.com", password=hashed_password, is_admin=True)
        db.session.add(admin)

    db.session.commit()
