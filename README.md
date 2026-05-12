# Medicine Finder

Python backend project built with Flask, SQLAlchemy, scraping utilities, and an OpenAI-compatible LLM API.

## Project Summary

Medicine Finder is a backend-focused web application for searching medicines, managing a cart, placing orders, importing medicine data through Python scraping, and using an AI assistant with tool routing and retrieval.

## Python And AI Topics Covered

- Python backend development
- Flask application structure with controllers and services
- REST-style request/response handling
- SQLAlchemy models and database operations
- User authentication with Flask-Login
- Password hashing with `bcrypt`
- SQLite database integration
- JSON API responses for search, chatbot, and checkout flows
- LLM API integration using the OpenAI Python SDK
- Agent-style planning and tool execution in Python
- Tool routing across inventory, orders, cart, and knowledge search
- Multi-turn chat history handling in Python
- Web scraping with `requests` and `BeautifulSoup`
- Retrieval over knowledge documents using embeddings / vector similarity
- Embedding reindex flow for knowledge documents
- Error handling and fallback logic for AI model calls
- Modular backend architecture for maintainability

## Role-Relevant Features

- Search API with filters for medicine name, price, and stock
- Cart and checkout backend flow
- Order history tracking
- Admin inventory management
- AI assistant integrated into the Python backend
- Agentic backend workflow for tool selection and response synthesis
- Scraped medicine import pipeline
- Vector-style retrieval for medicine guidance

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite
- OpenAI Python SDK
- Requests
- BeautifulSoup
- HTML
- Tailwind CSS

## Project Structure

```text
app/
  controllers/
  services/
  models.py
  extensions.py
  seed.py
templates/
app.py
requirements.txt
```

## Notes

- This project demonstrates Python backend, API, database, scraping, LLM integration, tool routing, and retrieval workflows.
- The retrieval layer uses a lightweight embedding pipeline with vector similarity and can work with API embeddings or local fallback embeddings.
