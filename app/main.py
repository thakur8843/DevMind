import logging
import logging.config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.db.database import Base, engine
from app.api.routes import review, health
from app.middleware import (
    LoggingMiddleware,
    limiter,
    rate_limit_exceeded_handler,
    register_error_handlers,
)

# ── Logging config ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

settings = get_settings()

# ── DB bootstrap ───────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DevMind API",
    description="Agentic code review platform — FastAPI · Qdrant · PostgreSQL · Groq",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware stack (order matters — outermost = first to run) ─────────────
#
#  Request  →  LoggingMiddleware  →  CORS  →  Route handler
#  Response ←  LoggingMiddleware  ←  CORS  ←  Route handler
#
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiter ───────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ── Global error handlers ──────────────────────────────────────────────────
register_error_handlers(app)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(review.router, prefix="/api/v1")
