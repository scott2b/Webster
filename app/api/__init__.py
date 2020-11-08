from enum import Enum, IntEnum
from typing import List, Optional
from pydantic import BaseModel, Field, constr, validator
from spectree import SpecTree, Response
from spectree.plugins.starlette_plugin import StarlettePlugin, PAGES
from starlette.applications import Starlette
from starlette.authentication import requires
from sqlalchemy import exc
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from ..config import settings
from ..orm.oauth2.token import oauth2_tokens
from ..orm.db import db_session, session_scope
from dependency_injector.wiring import Closing
from dependency_injector.wiring import Provide
from ..containers import Container


class APIExceptionResponse(BaseModel):

    status: int
    msg: str


async def api_exception(request, exc):
    return JSONResponse({
        "msg": exc.detail,
        "status": exc.status_code}, status_code=exc.status_code)


exception_handlers = {
    HTTPException: api_exception
}


UI_ROUTES = {
  'redoc': 'api',
  # 'swagger': 'swagger' # Swagger not yet supported due to need to sort out
                         # authentication and potentially csrf
}

class CustomPlugin(StarlettePlugin):

    def register_route(self, app):
        self.app = app
        try:
            self.app.add_route(
                self.config.spec_url,
                lambda request: JSONResponse(self.spectree.spec),
            )
        except: # some weirdness in the spectree library
            pass
        for ui in PAGES:
            if ui in UI_ROUTES:
                self.app.add_route(
                    f'/{self.config.PATH}/{UI_ROUTES[ui]}',
                    lambda request, ui=ui: HTMLResponse(
                        PAGES[ui].format(self.config.spec_url)
                    ),
                )

_app = SpecTree('starlette', path='docs', backend=CustomPlugin, MODE='strict')


class Message(BaseModel):
    message: str




class StatusEnum(str, Enum):
    ok = 'OK'
    err = 'ERR'


class ValidationError(BaseModel):
    loc: List[str]
    msg: str
    type: str


class ValidationErrorList(BaseModel):
    __root__: List[ValidationError]

    

class Profile(BaseModel):
    name: constr(min_length=2, max_length=40)  # Constrained Str
    age: int = Field(
        ...,
        gt=0,
        lt=150,
        description='user age(Human)'
    )


class Cookie(BaseModel):
    """Cookie model. Theoretically, we can pass this to SpecTree's validate
    decorator. However, Swagger does not currently support automatic
    submission of cookies with requests from the Swagger UI.
    """
    csrf_token: str

    @validator('csrf_token')
    def csrf_token_is_valid(cls, v):
        pass # TODO: implement authentication for Swagger support


@_app.validate(json=Profile, resp=Response(HTTP_200=Message, HTTP_403=None), tags=['api'])
@requires('app_auth', status_code=403)
async def user_profile(request):
    """
    verify user profile (summary of this endpoint)

    user's name, user's age, ... (long description)
    """
    print(request.context.json)  # or await request.json()
    return JSONResponse({'text': 'it works'})


@requires(['api_auth'], status_code=403)
async def widget(request):
    return JSONResponse({ 'foo': 'bar' })


#from .clients import clients_get, clients_delete, clients_list, clients_post
#from .tokens import token, token_refresh


from . import clients, tokens

routes = [
    Route('/user', user_profile, methods=['POST']),
    # clients
    Route('/clients/{client_id:str}', clients.clients_get, methods=['GET']),
    Route('/clients/{client_id:str}', clients.clients_delete, methods=['DELETE']),
    Route('/clients', clients.clients_list, methods=['GET']),
    Route('/clients', clients.clients_post, methods=['POST']),
    # tokens
    Route('/token', tokens.token_create, methods=['POST']),
    Route('/token-refresh', tokens.token_refresh, methods=['POST']),
    #
    Route('/widget/', widget)
]


def get_app():
    app = Starlette(
        debug=True,
        routes=routes,
        exception_handlers=exception_handlers,
        on_startup=[])
    _app.register(app)
    return app