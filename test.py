from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS test_connection"))
    conn.commit()

print("✅ Table deleted successfully!")