from .containers import Container
from .orm import db #, oauth2
from .orm import user, base
from .orm import oauth2client, oauth2token

def do_wiring():
    container = Container()
    container.init_resources()
    container.wire(modules=[db, base, user, oauth2client, oauth2token])
