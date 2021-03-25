from .containers import Container
from .orm import db #, oauth2
from .orm import user, base
from .orm import oauth2client, oauth2token

DEFAULT_MODULES = [db, base, user, oauth2client, oauth2token]

def do_wiring(modules=None):
    if modules is None:
        modules = DEFAULT_MODULES
    container = Container()
    container.init_resources()
    container.wire(modules=modules)
