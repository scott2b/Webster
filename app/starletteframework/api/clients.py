from spectree import Response
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from ...orm.oauth2client import OAuth2Client
from ...schemas.oauth2client import (
    OAuth2ClientCreate,
    OAuth2ClientResponse,
    OAuth2ClientRequest,
    OAuth2ClientListResponse)
from ...orm.db import db_session
#from .routes import _api, APIMessage, APIExceptionResponse
#from . import ValidationErrorList
from typing import List
from pydantic import BaseModel, validator, ValidationError
from spectree import SpecTree
from spectree.plugins.starlette_plugin import StarlettePlugin
from sqlalchemy import exc
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.routing import Route, Router
from ..templates import render


class APIMessage(BaseModel):

    status: int
    msg: str


class APIExceptionResponse(APIMessage):
    ...

async def api_exception(request, exc):
    return JSONResponse({
        "msg": exc.detail,
        "status": exc.status_code}, status_code=exc.status_code)

async def validation_error(request, exc):
    return JSONResponse(exc.errors(), status_code=422)


exception_handlers = {
    HTTPException: api_exception,
    ValidationError: validation_error
}


#UI_ROUTES = {
#  'redoc': 'api',
#  # 'swagger': 'swagger' # Swagger not yet supported due to need to sort out
#                         # authentication and potentially csrf
#}

class CustomPlugin(StarlettePlugin):


    def register_route(self, app):
        """Use standard routing."""
        self.app = app

    #def _register_route(self, app):
    #    self.app = app
    #    try:
    #        self.app.add_route(
    #            self.config.spec_url,
    #            lambda request: JSONResponse(self.spectree.spec),
    #        )
    #    except: # some weirdness in the spectree library
    #        pass
    #    for ui in PAGES:
    #        if ui in UI_ROUTES:
    #            self.app.add_route(
    #                f'/{self.config.PATH}/{UI_ROUTES[ui]}',
    #                lambda request, ui=ui: HTMLResponse(
    #                    PAGES[ui].format(self.config.spec_url)
    #                ),
    #            )

_app = SpecTree('starlette', path='docs', backend=CustomPlugin, MODE='strict')


class ValidationErrorMessage(BaseModel):
    loc: List[str]
    msg: str
    type: str


class ValidationErrorList(BaseModel):
    __root__: List[ValidationErrorMessage]
    

#class Profile(BaseModel):
#    name: constr(min_length=2, max_length=40)  # Constrained Str
#    age: int = Field(
#        ...,
#        gt=0,
#        lt=150,
#        description='user age(Human)'
#    )


class Cookie(BaseModel):
    """Cookie model. Theoretically, we can pass this to SpecTree's validate
    decorator. However, Swagger does not currently support automatic
    submission of cookies with requests from the Swagger UI.
    """
    csrf_token: str

    @validator('csrf_token')
    def csrf_token_is_valid(cls, v):
        pass # TODO: implement authentication for Swagger support


#@_app.validate(json=Profile, resp=Response(HTTP_200=APIMessage, HTTP_403=None), tags=['api'])
#@requires('app_auth', status_code=403)
#async def user_profile(request):
#    """
#    verify user profile (summary of this endpoint)
#
#    user's name, user's age, ... (long description)
#    """
#    print(request.context.json)  # or await request.json()
#    return JSONResponse({'msg': 'it works', 'status': 200})


#from . import clients #, tokens
from . import tokens
#from .users import profile, password
from . import users


PREFIX = '/v0.1'
SPEC_URL = '/docs/openapi.json'


def docs(request):
    return render('redoc.html', { 'spec_url': PREFIX + SPEC_URL })



@requires('api_auth', status_code=403)
@_app.validate(resp=Response(HTTP_200=OAuth2ClientListResponse,
                             HTTP_403=APIExceptionResponse), tags=['clients'])
@db_session
async def clients_list(request, db):
    """Get available clients."""
    user=request.scope['token'].get_user(db=db)
    clients = OAuth2Client.objects.fetch_for_user(user, db=db)
    r = OAuth2ClientListResponse(clients=[c.dict(model=OAuth2ClientResponse)
        for c in clients])
    return JSONResponse(r.dict(), status_code=200)


@requires('api_auth', status_code=403)
@_app.validate(resp=Response(HTTP_200=OAuth2ClientResponse,
                             HTTP_403=APIExceptionResponse,
                             HTTP_404=APIExceptionResponse), tags=['clients'])
@db_session
async def clients_get(request, db):
    """Get a specified client."""
    client_id = request.path_params.get('client_id')
    user=request.scope['token'].get_user(db=db)
    client = OAuth2Client.objects.get_for_user(user, client_id, db=db)
    if client:
        return JSONResponse(client.dict(model=OAuth2ClientResponse), status_code=200)
    raise HTTPException(404, detail="Not found")


@requires('api_auth', status_code=403)
@_app.validate(resp=Response(HTTP_200=APIMessage,
                             HTTP_403=APIExceptionResponse,
                             HTTP_404=APIExceptionResponse), tags=['clients'])
@db_session
async def clients_delete(request, db):
    """Delete a client."""
    client_id = request.path_params.get('client_id')
    user=request.scope['token'].get_user(db=db)
    r = OAuth2Client.objects.delete_for_user(user, client_id, db=db)
    if r:
        return JSONResponse(APIMessage(msg='Deleted', status=200).dict(),
            status_code=200)
    raise HTTPException(404, detail="Not found")


@requires('api_auth', status_code=403)
@_app.validate(json=OAuth2ClientRequest,
               resp=Response(HTTP_201=OAuth2ClientResponse,
                             HTTP_403=APIExceptionResponse,
                             HTTP_409=ValidationErrorList,
                             HTTP_422=ValidationErrorList), tags=['clients'])
async def clients_post(request):
    """Create a client."""
    data = await request.json()
    try:
        user = request.scope['token'].get_user()
        _client = OAuth2Client.objects.create(
            OAuth2ClientCreate(user=user, **data))
    except OAuth2Client.Exists:
        return JSONResponse([ { 'loc': ['name'],
            'msg': 'Client name already exists for account.',
            'type': 'value_error.name_exists' }],
            status_code=409)
    return JSONResponse(_client.dict(model=OAuth2ClientResponse), status_code=201)


router = Router(
    routes = [
        #Route('/user', user_profile, methods=['POST']),
        Route('/profile', users.profile, methods=['GET', 'PUT']),
        Route('/password', users.password, methods=['PUT']),
        # clients
        Route('/clients/{client_id:str}', clients_get, methods=['GET']),
        Route('/clients/{client_id:str}', clients_delete, methods=['DELETE']),
        Route('/clients', clients_list, methods=['GET']),
        Route('/clients', clients_post, methods=['POST']),
        # tokens
        Route('/token', tokens.token_create, methods=['POST']),
        Route('/token-refresh', tokens.token_refresh, methods=['POST']),
        Route(SPEC_URL, lambda request:JSONResponse(_app.spec)),
        Route('/docs/api', docs, name='api_docs', methods=['GET']),
        #Route('/docs/api', lambda request, ui='redoc': HTMLResponse(
        #    PAGES['redoc'].format(PREFIX+SPEC_URL)))
    ]
)
_app.register(router)
