import json
import re

from .ai_client_service import create_chat_completion
from .knowledge_service import get_relevant_documents
from .medicine_service import search_medicines_for_agent
from .order_service import get_user_orders, summarize_orders_for_agent


def build_cart_summary(cart_items):
    if not cart_items:
        return "Cart is empty."

    total = sum(item.get("price", 0) * item.get("quantity", 0) for item in cart_items)
    lines = [
        f"{item.get('name', 'Unknown')}: {item.get('quantity', 0)} x Rs. {item.get('price', 0):.2f}"
        for item in cart_items
    ]
    return "Cart items:\n" + "\n".join(lines) + f"\nTotal: Rs. {total:.2f}"


def heuristic_plan(user_input):
    lowered = user_input.lower()
    tools = []
    medicine_query = None

    if any(keyword in lowered for keyword in ["stock", "price", "available", "availability", "medicine", "tablet"]):
        tools.append("inventory_search")
        words = re.findall(r"[a-zA-Z]+", user_input)
        medicine_query = " ".join(words[-3:]).strip() or user_input

    if any(keyword in lowered for keyword in ["order", "orders", "history", "bought", "purchased"]):
        tools.append("order_lookup")

    if any(keyword in lowered for keyword in ["cart", "checkout", "total"]):
        tools.append("cart_summary")

    if any(keyword in lowered for keyword in ["use", "dosage", "take", "side effect", "antibiotic", "fever", "pain"]):
        tools.append("knowledge_lookup")

    if not tools:
        tools.append("general_llm")

    return {
        "intent": "assistant_request",
        "tools": list(dict.fromkeys(tools)),
        "medicine_query": medicine_query,
    }


def llm_plan(user_input):
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a planner for a Python backend medicine assistant. "
                "Return strict JSON with keys intent, tools, medicine_query. "
                "Available tools: inventory_search, order_lookup, cart_summary, knowledge_lookup, general_llm. "
                "Choose only relevant tools."
            ),
        },
        {"role": "user", "content": user_input},
    ]

    try:
        response = create_chat_completion(prompt, max_tokens=150, temperature=0)
        return json.loads(response)
    except Exception:
        return heuristic_plan(user_input)


def execute_tools(user_id, user_input, plan, cart_items):
    tool_outputs = []

    if "inventory_search" in plan.get("tools", []):
        results = search_medicines_for_agent(plan.get("medicine_query") or user_input, limit=5)
        if results:
            formatted = "\n".join(
                f"- {medicine.name}: Rs. {medicine.price:.2f}, stock {medicine.quantity}"
                for medicine in results
            )
        else:
            formatted = "No matching medicines found."
        tool_outputs.append(f"Inventory results:\n{formatted}")

    if "order_lookup" in plan.get("tools", []):
        tool_outputs.append(summarize_orders_for_agent(get_user_orders(user_id)))

    if "cart_summary" in plan.get("tools", []):
        tool_outputs.append(build_cart_summary(cart_items))

    if "knowledge_lookup" in plan.get("tools", []):
        documents = get_relevant_documents(user_input, limit=3)
        if documents:
            formatted = "\n".join(f"- {document.title}: {document.content}" for document in documents)
            tool_outputs.append(f"Knowledge results:\n{formatted}")
        else:
            tool_outputs.append("Knowledge results:\nNo related guidance found.")

    return tool_outputs


def synthesize_response(user_input, tool_outputs):
    if not tool_outputs:
        tool_outputs = ["No backend tool output available."]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Python backend medicine assistant. "
                "Use the provided tool outputs. "
                "Be direct. Mention when results come from inventory or order data. "
                "For medical safety, advise consulting a doctor when needed."
            ),
        },
        {
            "role": "user",
            "content": (
                f"User request:\n{user_input}\n\n"
                f"Tool outputs:\n" + "\n\n".join(tool_outputs)
            ),
        },
    ]

    try:
        return create_chat_completion(messages, max_tokens=220, temperature=0.2)
    except Exception:
        return "\n\n".join(tool_outputs)


def run_agentic_chat(user_id, user_input, cart_items=None):
    plan = llm_plan(user_input)
    tool_outputs = execute_tools(user_id, user_input, plan, cart_items or [])
    response = synthesize_response(user_input, tool_outputs)
    return {
        "response": response,
        "plan": plan,
        "tool_outputs": tool_outputs,
    }
