"""
Handle dependency injection wiring first thing.  Experimental attempts at wiring
routing modules has not gone well. Note that dependency injection is very
sensitive to how imports are done. From the docs:

Python has a limitation on patching already imported individual members. To
protect from errors prefer an import of modules instead of individual members
or make sure that imports happen after the wiring.
https://python-dependency-injector.ets-labs.org/wiring.html

However, attempts to cleanup the imports in the api module have not led to
successful patching of that module. For the time being, settling with using
a decorator for db session management and only injecting into the decorator
(actually via a helper method).
"""
from .containers import Container
from .orm import db #, oauth2
from .orm import user, base
from .orm.oauth2 import client, token
container = Container()
container.init_resources()
#container.config.from_ini('config.ini')
import sys
container.wire(modules=[db, user, client, token])
# TODO: why can't we do this? The api module in particular seems problematic:
# container.wire(modules=[db, ui, api])
from . import ui, api

# end of wiring

from dependency_injector.wiring import Provide
from starlette.applications import Starlette
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Route, Mount, WebSocketRoute, Router
from starlette.staticfiles import StaticFiles
from .config import settings
from .auth import backend


class CustomMiddleware(BaseHTTPMiddleware):
    """From: https://github.com/encode/starlette/blob/7f8cd041734be3b290cdb178e99c37e1d5a19b41/tests/middleware/test_base.py#L11

    Example of Custom Middleware. Add to app below with `add_middleware` if implemented.
    """
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Custom-Header"] = "Example"
        return response


def startup():
    print(f'{settings.PROJECT_NAME} startup.')




app_routes = [
    Route('/', ui.homepage, methods=['GET', 'POST']),
    Route('/logout', ui.logout),
    Mount('/static', StaticFiles(directory="static"), name='static'),
    Mount('', app=api.get_app()),
]

app = Starlette(
    debug=True,
    routes=app_routes,
    on_startup=[startup])


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.add_middleware(
    AuthenticationMiddleware,
    backend=backend.SessionAuthBackend())


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE,
    max_age=settings.SESSION_EXPIRE_SECONDS,
    same_site=settings.SESSION_SAME_SITE,
    https_only=False)

