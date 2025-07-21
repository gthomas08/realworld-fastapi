from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from src.config import settings


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy for authentication."""
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)


# Configure the authentication transport and backend
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
