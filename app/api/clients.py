from typing import List
from pydantic import BaseModel
from spectree import SpecTree, Response
from starlette.authentication import requires
from starlette.responses import JSONResponse
from ..orm.oauth2.client import OAuth2Client
from ..orm.oauth2.client import OAuth2ClientCreate, OAuth2Base
from ..orm.db import db_session, session_scope
from . import _app, Message


class OAuth2ClientSchema(BaseModel):
    name: str


class OAuth2ClientDelete(BaseModel):
    client_id: str

class OAuth2ClientResp(BaseModel):
    client_id: str
    client_secret: str


class ValidationError(BaseModel):
    loc: List[str]
    msg: str
    type: str


class ValidationErrorList(BaseModel):
    __root__: List[ValidationError]


class OAuth2ClientList(BaseModel):
    __root__: List[OAuth2ClientResp]


class OAuth2ClientResponse(BaseModel):
    clients: List[OAuth2ClientResp]

@requires('api_auth', status_code=403)
@_app.validate(resp=Response(HTTP_200=OAuth2ClientResponse, # OAuth2ClientResp,
                             HTTP_403=None,
                             HTTP_404=None,
                             HTTP_422=ValidationErrorList), tags=['clients'])
@db_session
async def client_list(request, db):
    """Get available clients."""
    user=request.scope['token'].get_user(db=db)
    clients = OAuth2Client.objects.get_by_user_id(user.id)
    r = { 'clients': [ { 'client_id': c.client_id, 'client_secret': c.client_secret }
        for c in clients ] }
    return JSONResponse(r, status_code=200)
    return JSONResponse({ 'message': 'Not found' }, status_code=404)


@requires('api_auth', status_code=403)
@_app.validate(resp=Response(HTTP_200=OAuth2ClientResp,
                             HTTP_403=None,
                             HTTP_404=None,
                             HTTP_422=ValidationErrorList), tags=['clients'])
@db_session
async def clients_get(request, db):
    """Get a specified client."""
    client_id = request.path_params.get('client_id')
    user=request.scope['token'].get_user(db=db)
    client = OAuth2Client.objects.get_by_client_id_user(client_id, user.id)
    if client:
        return JSONResponse( {
            'client_id': client.client_id,
            'client_secret': client.client_secret }, status_code=200)
    return JSONResponse({ 'message': 'Not found' }, status_code=404)


@requires('api_auth', status_code=403)
@_app.validate(resp=Response(HTTP_200=Message,
                             HTTP_403=None,
                             HTTP_404=None,
                             HTTP_422=ValidationErrorList), tags=['clients'])
@db_session
async def clients_delete(request, db):
    """Delete a client."""
    client_id = request.path_params.get('client_id')
    user=request.scope['token'].get_user(db=db)
    if request.method == 'DELETE':
        r = OAuth2Client.objects.delete_user_client(client_id, user, db=db)
        if r:
            return JSONResponse({ 'message': 'Deleted' }, status_code=200)
    return JSONResponse({ 'message': 'Not found' }, status_code=404)


@requires('api_auth', status_code=403)
@_app.validate(json=OAuth2ClientSchema,
               resp=Response(HTTP_201=OAuth2ClientResp,
                             HTTP_403=None,
                             HTTP_409=ValidationErrorList,
                             HTTP_422=ValidationErrorList), tags=['clients'])
async def client_post(request):
    """Create a client."""
    data = await request.json()
    obj = OAuth2ClientCreate(
        name=data['name'],
        user=request.scope['token'].get_user()
    )
    try:
        _client = OAuth2Client.objects.create(obj_in=obj)
    except exc.IntegrityError:
        return JSONResponse([ { 'loc': ['name'],
            'msg': 'Client name already exists for account.',
            'type': 'value_error.name_exists' }],
            status_code=409)
    return JSONResponse({
        'client_id': _client.client_id,
        'client_secret': _client.client_secret,
    }, status_code=201)

