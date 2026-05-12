from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..services.agent_service import run_agentic_chat
from ..services.chat_service import get_user_chats, save_chat_message
from ..services.knowledge_service import rebuild_knowledge_embeddings
from ..services.medicine_service import (
    add_medicine,
    delete_medicine,
    get_all_medicines,
    search_medicines,
    update_medicine,
)
from ..services.order_service import create_order
from ..services.scraper_service import scrape_and_import_medicines

medicine_bp = Blueprint("medicine", __name__)


@medicine_bp.route("/admin", methods=["GET", "POST"], endpoint="admin")
@login_required
def admin():
    if not current_user.is_admin:
        flash("Access denied. Admins only.", "error")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            add_medicine(
                name=request.form.get("name"),
                quantity=int(request.form.get("quantity")),
                price=float(request.form.get("price")),
            )
        elif action == "edit":
            update_medicine(
                medicine_id=int(request.form.get("id")),
                name=request.form.get("name"),
                quantity=int(request.form.get("quantity")),
                price=float(request.form.get("price")),
            )
        elif action == "delete":
            delete_medicine(int(request.form.get("id")))
        elif action == "scrape_sample":
            result = scrape_and_import_medicines("sample")
            flash(f"Imported {result['count']} medicines from sample source.", "success")
            return redirect(url_for("medicine.admin"))
        elif action == "scrape_url":
            source_url = request.form.get("source_url", "").strip()
            if not source_url:
                flash("Source URL is required.", "error")
                return redirect(url_for("medicine.admin"))
            try:
                result = scrape_and_import_medicines(source_url)
                flash(f"Imported {result['count']} medicines from source.", "success")
            except Exception as error:
                flash(f"Scrape failed: {error}", "error")
            return redirect(url_for("medicine.admin"))
        elif action == "reindex_knowledge":
            count = rebuild_knowledge_embeddings()
            flash(f"Rebuilt embeddings for {count} knowledge documents.", "success")
            return redirect(url_for("medicine.admin"))

        flash("Medicine updated successfully.", "success")
        return redirect(url_for("medicine.admin"))

    medicines = get_all_medicines()
    return render_template("admin.html", medicines=medicines)


@medicine_bp.route("/search", methods=["GET", "POST"], endpoint="search_medicine")
def search_medicine():
    if request.method == "POST":
        medicines = search_medicines(
            medicine_name=request.form.get("medicine_name", "").strip(),
            min_price=request.form.get("min_price", type=float),
            max_price=request.form.get("max_price", type=float),
            min_stock=request.form.get("min_stock", type=int),
            page=request.form.get("page", 1, type=int),
            per_page=6,
        )

        results = [
            {"id": item.id, "name": item.name, "quantity": item.quantity, "price": item.price}
            for item in medicines.items
        ]
        return jsonify(
            {
                "results": results,
                "has_next": medicines.has_next,
                "has_prev": medicines.has_prev,
                "page": medicines.page,
                "total_pages": medicines.pages,
            }
        )

    return render_template("search.html")


@medicine_bp.route("/chatbot", methods=["GET", "POST"], endpoint="chatbot")
@login_required
def chatbot():
    if request.method == "POST":
        payload = request.get_json() or {}
        user_input = payload.get("message")
        conversation_history = payload.get("history", [])
        cart_items = payload.get("cart", [])

        try:
            agent_result = run_agentic_chat(
                user_id=current_user.id,
                user_input=user_input,
                cart_items=cart_items,
            )
        except ValueError as error:
            return jsonify({"error": str(error)}), 503
        except Exception:
            return jsonify({"error": "Chat service is temporarily unavailable."}), 500

        response = agent_result["response"]
        save_chat_message(current_user.id, user_input, response)

        updated_history = conversation_history + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response},
        ]
        return jsonify(
            {
                "response": response,
                "history": updated_history,
                "plan": agent_result["plan"],
                "tool_outputs": agent_result["tool_outputs"],
            }
        )

    chats = get_user_chats(current_user.id)
    return render_template("chatbot.html", chats=chats)


@medicine_bp.route("/cart", methods=["GET"], endpoint="cart")
@login_required
def cart():
    return render_template("cart.html")


@medicine_bp.route("/checkout", methods=["POST"], endpoint="checkout")
@login_required
def checkout():
    payload = request.get_json() or {}
    cart_items = payload.get("cart", [])
    response_body, status_code = create_order(current_user.id, cart_items)
    return jsonify(response_body), status_code
