from spectree import Response
from starlette.authentication import requires
from starlette.responses import JSONResponse
from pydantic import BaseModel
from ..config import settings
from ..orm.oauth2.client import OAuth2Client
from ..orm.oauth2.token import OAuth2Token
from . import _app, ValidationErrorList


class TokenRequest(BaseModel):
    grant_type:str
    client_id:str
    client_secret:str


class TokenRefreshRequest(BaseModel):
    grant_type: str
    refresh_token: str
    access_lifetime: int
    refresh_lifetime: int


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

# OAuth2 spec seems to mandate form data for token request:
# https://github.com/requests/requests-oauthlib/issues/244

@_app.validate(json=None,
               resp=Response(HTTP_201=TokenResponse,
                             HTTP_403=None,
                             HTTP_409=ValidationErrorList,
                             HTTP_422=ValidationErrorList), tags=['tokens'])
async def token_refresh(request):
    data = dict(await request.form())
    data['access_lifetime'] = settings.OAUTH2_ACCESS_TOKEN_TIMEOUT_SECONDS
    data['refresh_lifetime'] = settings.OAUTH2_REFRESH_TOKEN_TIMEOUT_SECONDS
    if 'allow_redirects' in data:
        del data['allow_redirects']
    req = TokenRefreshRequest(**data) 
    token = OAuth2Token.objects.refresh(**data)
    return JSONResponse(token.response_data())



@_app.validate(json=None,
               resp=Response(HTTP_201=TokenResponse,
                             HTTP_403=None,
                             HTTP_409=ValidationErrorList,
                             HTTP_422=ValidationErrorList), tags=['tokens'])
async def token(request):
    data = dict(await request.form())
    req = TokenRequest(**data)
    data['access_lifetime'] = settings.OAUTH2_ACCESS_TOKEN_TIMEOUT_SECONDS
    data['refresh_lifetime'] = settings.OAUTH2_REFRESH_TOKEN_TIMEOUT_SECONDS
    try:
        token = OAuth2Token.objects.create(**data)
    except (OAuth2Client.DoesNotExist, OAuth2Client.InvalidOAuth2Client,
            OAuth2Token.InvalidGrantType) as e:
        return JSONResponse({ 'message': str(e) }, status_code=403)
    return JSONResponse(token.response_data())

