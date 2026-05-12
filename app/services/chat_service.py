import os

from openai import OpenAI

from ..extensions import db
from ..models import Chat

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
client = None


def get_openrouter_client():
    global client

    if client is not None:
        return client

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in .env file. Please add it.")

    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
    return client


def get_ai_response(user_input, conversation_history=None):
    client_instance = get_openrouter_client()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant for a Medicine Availability Finder app. "
                "Respond concisely and helpfully. If the user asks about medicine availability, "
                "price, or stock, suggest they use the search bar but offer insights based on "
                "common knowledge. For general health queries, advise consulting a doctor. "
                "Keep responses under 150 words."
            ),
        }
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": user_input})

    model_priority = [
        "meta-llama/llama-3.1-8b-instruct",
        "google/gemma-7b-it",
        "nousresearch/hermes-2-pro-mistral",
    ]

    for model in model_priority:
        try:
            response = client_instance.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=200,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as error:
            print(f"[WARN] Model {model} failed: {error}")

    return "Sorry, I encountered an issue with all available AI models. Please try again later."


def save_chat_message(user_id, message, response):
    chat = Chat(user_id=user_id, message=message, response=response)
    db.session.add(chat)
    db.session.commit()
    return chat


def get_user_chats(user_id):
    return Chat.query.filter_by(user_id=user_id).order_by(Chat.timestamp.asc()).all()
