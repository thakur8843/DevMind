"""Run once to create all PostgreSQL tables."""
from app.db.database import Base, engine
from app.models import review  # noqa: F401 — registers models with Base

print("Creating PostgreSQL tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created: code_reviews, chat_history, request_logs")
