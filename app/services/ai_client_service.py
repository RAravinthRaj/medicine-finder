import os

from openai import OpenAI

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
CHAT_MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "google/gemma-7b-it",
    "nousresearch/hermes-2-pro-mistral",
]
EMBEDDING_MODELS = [
    os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
]

client = None


def get_client():
    global client

    if client is not None:
        return client

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in .env file. Please add it.")

    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    return client


def create_chat_completion(messages, max_tokens=250, temperature=0.2):
    client_instance = get_client()

    for model in CHAT_MODELS:
        try:
            response = client_instance.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as error:
            print(f"[WARN] Chat model {model} failed: {error}")

    raise RuntimeError("All configured chat models failed.")


def create_embedding(text):
    client_instance = get_client()

    for model in EMBEDDING_MODELS:
        try:
            response = client_instance.embeddings.create(model=model, input=text)
            return response.data[0].embedding
        except Exception as error:
            print(f"[WARN] Embedding model {model} failed: {error}")

    raise RuntimeError("All configured embedding models failed.")
