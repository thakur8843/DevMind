"""
Run once after init_db.py.
Creates LangGraph checkpoint tables in PostgreSQL for Phase 2.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from langgraph.checkpoint.postgres import PostgresSaver
from app.core.config import get_settings

settings = get_settings()

print("Connecting to PostgreSQL...")
try:
    checkpointer = PostgresSaver.from_conn_string(settings.database_url)
    checkpointer.setup()
    print("✅ Tables created:")
    print("   → langgraph_checkpoints")
    print("   → langgraph_checkpoint_blobs")
    print("   → langgraph_checkpoint_writes")
except Exception as e:
    print(f"❌ Failed: {e}")