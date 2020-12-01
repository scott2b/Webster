from ..wiring import do_wiring

do_wiring()

from starlette.applications import Starlette
from .middleware import setup_middleware
from .routing import routes
from ..config import settings


def startup():
    print(f'{settings.PROJECT_NAME} startup.')


app = Starlette(
    debug=True,
    routes=routes,
    on_startup=[startup])

setup_middleware(app)
