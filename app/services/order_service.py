from ..extensions import db
from ..models import Medicine, Order, OrderItem


def get_user_orders(user_id):
    return Order.query.filter_by(user_id=user_id).order_by(Order.date.desc()).all()


def create_order(user_id, cart_items):
    if not cart_items:
        return {"error": "Cart is empty"}, 400

    total = 0
    order = Order(user_id=user_id, total=0)
    db.session.add(order)

    for item in cart_items:
        medicine_id = item.get("id")
        if not medicine_id:
            db.session.rollback()
            return {"error": f'Missing ID for item {item.get("name", "unknown")}'}, 400

        try:
            item_total = item["price"] * item["quantity"]
        except (KeyError, TypeError):
            db.session.rollback()
            return {"error": f'Invalid price or quantity for item {item.get("name", "unknown")}'}, 400

        medicine = Medicine.query.get(medicine_id)
        if not medicine:
            db.session.rollback()
            return {"error": f'Medicine {item.get("name", "unknown")} not found in database'}, 400

        if medicine.quantity < item["quantity"]:
            db.session.rollback()
            return {"error": f'Insufficient stock for {item["name"]}'}, 400

        total += item_total
        medicine.quantity -= item["quantity"]
        order_item = OrderItem(
            order=order,
            medicine_id=medicine.id,
            quantity=item["quantity"],
            price=item["price"],
        )
        db.session.add(order_item)

    order.total = total

    try:
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return {"error": f"Checkout failed: {str(error)}"}, 500

    return {"message": f"Checkout successful! Total amount: ₹{total:.2f}"}, 200
