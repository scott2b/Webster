from starlette.applications import Starlette
from .middleware import setup_middleware
from .routing import routes, startup


app = Starlette(
    debug=True,
    routes=routes,
    on_startup=[startup])

setup_middleware(app)
