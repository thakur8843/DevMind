from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from app.core.config import get_settings

settings = get_settings()


def hash_password(plain: str) -> str:
    """Hash password using bcrypt directly — no passlib."""
    password_bytes = plain.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against bcrypt hash."""
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8"),
    )


def create_access_token(user_id: int) -> str:
    """
    Create signed JWT.
    Payload: { sub: user_id, exp: now + 30mins }
    """
    expire = datetime.utcnow() + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.app_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """
    Decode and verify JWT.
    Raises ValueError if expired or tampered.
    """
    try:
        return jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=["HS256"],
        )
    except JWTError:
        raise ValueError("Invalid or expired token")