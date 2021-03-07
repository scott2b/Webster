"""
Middleware configurations.
"""
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from ..config import settings
from . import backends


class CustomMiddleware(BaseHTTPMiddleware):
    """From: https://github.com/encode/starlette/blob/7f8cd041734be3b290cdb178e99c37e1d5a19b41/tests/middleware/test_base.py#L11

    Example of Custom Middleware. Add to app below with `add_middleware` if
    implemented. Here for documentation purposes.
    """
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Custom-Header"] = "Example"
        return response


def setup_middleware(app):
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS)
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(
        AuthenticationMiddleware,
        backend=backends.SessionAuthBackend())
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        session_cookie=settings.SESSION_COOKIE,
        max_age=settings.SESSION_EXPIRE_SECONDS,
        same_site=settings.SESSION_SAME_SITE,
        https_only=False)
