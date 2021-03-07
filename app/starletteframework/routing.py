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
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from . import user, auth, api, oauth2, admin, docs
from . import user, auth
from .api.clients import router

routes = [
    Route('/', user.homepage, name='home', methods=['GET', 'POST']),
    Route('/apps', oauth2.client_apps, name='apps', methods=['GET', 'POST']),
    Route('/docs/userdoc', docs.docs, name='docs', methods=['GET']),
    Mount('/static', StaticFiles(directory="static"), name='static'),
    Mount('/auth', app=auth.router, name='auth'),
    Route('/profile', user.profile, name='user_profile', methods=['GET', 'POST']),
    Mount('/admin', admin.router, name='admin'),
    #Mount('/v0.1', app=api.router),
]

