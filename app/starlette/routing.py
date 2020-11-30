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
from . import ui, auth, api, oauth2, admin

# end of wiring

from starlette.routing import Route, Mount, WebSocketRoute, Router
from starlette.staticfiles import StaticFiles
from ..config import settings


def startup():
    print(f'{settings.PROJECT_NAME} startup.')


routes = [
    Route('/', ui.homepage, methods=['GET', 'POST']),
    Route('/apps', oauth2.client_apps, methods=['GET', 'POST']),
    Mount('/static', StaticFiles(directory="static"), name='static'),
    Mount('/auth', app=auth.router),
    Route('/users/me', ui.update_user, methods=['GET', 'POST']),
    Mount('/admin/users', app=ui.router),
    Route('/admin', admin.admin, methods=['GET', 'POST']),
    Mount('/v0.1', app=api.router),
]

