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
from ..containers import Container
from ..orm import db #, oauth2
from ..orm import user, base
from ..orm import oauth2client, oauth2token
container = Container()
container.init_resources()
#container.config.from_ini('config.ini')
import sys
container.wire(modules=[db, base, user, oauth2client, oauth2token])
# TODO: why can't we do this? The api module in particular seems problematic:
# container.wire(modules=[db, ui, api])
from . import ui, auth, api

# end of wiring

from starlette.applications import Starlette
from starlette.routing import Route, Mount, WebSocketRoute, Router
from starlette.staticfiles import StaticFiles
from ..config import settings
from .middleware import setup_middleware


def startup():
    print(f'{settings.PROJECT_NAME} startup.')


app_routes = [
    Route('/', ui.homepage, methods=['GET', 'POST']),
    Route('/users/me', ui.update_user, methods=['GET', 'POST']),
    Route('/users/{user_id:int}', ui.update_user, methods=['GET', 'POST']),
    Route('/users', ui.users, methods=['GET']),
    Route('/login', auth.login, methods=['GET', 'POST']),
    Route('/logout', auth.logout),
    #Route('/users', ui.user, methods=['GET', 'POST']),
    Route('/verify', auth.password_reset, methods=['GET']),
    Route('/client-form', ui.client_form, methods=['POST']),
    Mount('/static', StaticFiles(directory="static"), name='static'),
    Mount('', app=api.get_app()),
]

app = Starlette(
    debug=True,
    routes=app_routes,
    on_startup=[startup])

setup_middleware(app)
