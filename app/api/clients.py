from spectree import Response
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from ..orm.oauth2.client import (
    OAuth2Client,
    OAuth2ClientCreate,
    OAuth2ClientResponse,
    OAuth2ClientRequest,
    OAuth2ClientListResponse)
from ..orm.db import db_session
from . import _app, Message, APIExceptionResponse
from . import ValidationErrorList


@requires('api_auth', status_code=403)
@_app.validate(resp=Response(HTTP_200=OAuth2ClientListResponse,
                             HTTP_403=APIExceptionResponse,
                             HTTP_422=ValidationErrorList), tags=['clients'])
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
                             HTTP_404=APIExceptionResponse,
                             HTTP_422=ValidationErrorList), tags=['clients'])
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
@_app.validate(resp=Response(HTTP_200=Message,
                             HTTP_403=APIExceptionResponse,
                             HTTP_404=APIExceptionResponse,
                             HTTP_422=ValidationErrorList), tags=['clients'])
@db_session
async def clients_delete(request, db):
    """Delete a client."""
    client_id = request.path_params.get('client_id')
    user=request.scope['token'].get_user(db=db)
    r = OAuth2Client.objects.delete_for_user(user, client_id, db=db)
    if r:
        return JSONResponse({ 'message': 'Deleted' }, status_code=200)
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
            OAuth2ClientCreate(name=data['name'], user=user))
    except OAuth2Client.Exists:
        return JSONResponse([ { 'loc': ['name'],
            'msg': 'Client name already exists for account.',
            'type': 'value_error.name_exists' }],
            status_code=409)
    return JSONResponse(_client.dict(model=OAuth2ClientResponse), status_code=201)

