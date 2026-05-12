from ..extensions import db
from ..models import Medicine


def get_all_medicines():
    return Medicine.query.all()


def add_medicine(name, quantity, price):
    medicine = Medicine(name=name, quantity=quantity, price=price)
    db.session.add(medicine)
    db.session.commit()
    return medicine


def upsert_medicine(name, quantity, price):
    medicine = Medicine.query.filter(Medicine.name.ilike(name)).first()
    if medicine:
        medicine.quantity = quantity
        medicine.price = price
    else:
        medicine = Medicine(name=name, quantity=quantity, price=price)
        db.session.add(medicine)
    db.session.commit()
    return medicine


def update_medicine(medicine_id, name, quantity, price):
    medicine = Medicine.query.get(medicine_id)
    if medicine:
        medicine.name = name
        medicine.quantity = quantity
        medicine.price = price
        db.session.commit()
    return medicine


def delete_medicine(medicine_id):
    medicine = Medicine.query.get(medicine_id)
    if medicine:
        db.session.delete(medicine)
        db.session.commit()
    return medicine


def search_medicines(medicine_name="", min_price=None, max_price=None, min_stock=None, page=1, per_page=6):
    query = Medicine.query.filter(Medicine.name.ilike(f"%{medicine_name}%"))

    if min_price is not None:
        query = query.filter(Medicine.price >= min_price)
    if max_price is not None:
        query = query.filter(Medicine.price <= max_price)
    if min_stock is not None:
        query = query.filter(Medicine.quantity >= min_stock)

    return query.paginate(page=page, per_page=per_page, error_out=False)


def search_medicines_for_agent(medicine_name="", limit=5):
    query = Medicine.query
    if medicine_name:
        query = query.filter(Medicine.name.ilike(f"%{medicine_name}%"))
    return query.order_by(Medicine.quantity.desc()).limit(limit).all()
