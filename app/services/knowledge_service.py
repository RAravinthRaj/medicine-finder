import hashlib
import json
import math
import re

from ..extensions import db
from ..models import KnowledgeDocument
from .ai_client_service import create_embedding

EMBEDDING_SIZE = 128
WORD_PATTERN = re.compile(r"[a-zA-Z0-9]+")

DEFAULT_KNOWLEDGE_DOCUMENTS = [
    {
        "title": "Paracetamol use",
        "content": (
            "Paracetamol is commonly used for fever and mild to moderate pain. "
            "Users should follow dosage guidance and consult a doctor for persistent symptoms."
        ),
        "doc_type": "faq",
        "source": "internal",
    },
    {
        "title": "Ibuprofen guidance",
        "content": (
            "Ibuprofen is commonly used for pain and inflammation. It should be taken with proper guidance, "
            "especially for users with stomach, kidney, or blood pressure concerns."
        ),
        "doc_type": "faq",
        "source": "internal",
    },
    {
        "title": "Antibiotic reminder",
        "content": (
            "Antibiotics such as amoxicillin should only be used on medical advice. "
            "Availability in the app does not replace a prescription or clinical guidance."
        ),
        "doc_type": "faq",
        "source": "internal",
    },
    {
        "title": "Medicine availability support",
        "content": (
            "For price, stock, and order status, the backend tools should query the database directly. "
            "The assistant should use live inventory results instead of guessing."
        ),
        "doc_type": "policy",
        "source": "internal",
    },
]


def tokenize(text):
    return WORD_PATTERN.findall(text.lower())


def build_local_embedding(text):
    vector = [0.0] * EMBEDDING_SIZE

    for token in tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        index = int(digest, 16) % EMBEDDING_SIZE
        vector[index] += 1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector

    return [value / norm for value in vector]


def get_embedding_for_text(text):
    try:
        return create_embedding(text)
    except Exception:
        return build_local_embedding(text)


def serialize_embedding(vector):
    return json.dumps(vector)


def deserialize_embedding(value):
    if not value:
        return None
    return json.loads(value)


def cosine_similarity(left, right):
    if not left or not right:
        return 0.0

    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return numerator / (left_norm * right_norm)


def seed_knowledge_documents():
    if KnowledgeDocument.query.first():
        return

    for document in DEFAULT_KNOWLEDGE_DOCUMENTS:
        content = f"{document['title']}. {document['content']}"
        db.session.add(
            KnowledgeDocument(
                title=document["title"],
                content=document["content"],
                doc_type=document["doc_type"],
                source=document["source"],
                embedding=serialize_embedding(get_embedding_for_text(content)),
            )
        )

    db.session.commit()


def rebuild_knowledge_embeddings():
    documents = KnowledgeDocument.query.all()
    for document in documents:
        content = f"{document.title}. {document.content}"
        document.embedding = serialize_embedding(get_embedding_for_text(content))
    db.session.commit()
    return len(documents)


def get_relevant_documents(query, limit=3):
    documents = KnowledgeDocument.query.all()
    if not documents:
        return []

    query_embedding = get_embedding_for_text(query)
    scored_documents = []

    for document in documents:
        embedding = deserialize_embedding(document.embedding)
        if embedding is None:
            content = f"{document.title}. {document.content}"
            embedding = get_embedding_for_text(content)
            document.embedding = serialize_embedding(embedding)
        score = cosine_similarity(query_embedding, embedding)
        scored_documents.append((score, document))

    db.session.commit()
    scored_documents.sort(key=lambda item: item[0], reverse=True)
    return [document for score, document in scored_documents[:limit] if score > 0]
