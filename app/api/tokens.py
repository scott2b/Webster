from spectree import Response
from starlette.responses import JSONResponse
from ..config import settings
from ..orm.oauth2.client import OAuth2Client
from ..orm.oauth2.token import OAuth2Token
from ..orm.oauth2.token import TokenResponse, TokenRequest, TokenRefreshRequest
from . import _app, ValidationErrorList


# OAuth2 spec seems to mandate form data (not json) for a token request:
# https://github.com/requests/requests-oauthlib/issues/244

@_app.validate(json=None,
               resp=Response(HTTP_201=TokenResponse,
                             HTTP_403=None,
                             HTTP_409=ValidationErrorList,
                             HTTP_422=ValidationErrorList), tags=['tokens'])
async def token_refresh(request):
    data = TokenRefreshRequest(**dict(await request.form())).dict()
    token = OAuth2Token.objects.refresh(
        access_lifetime = settings.OAUTH2_ACCESS_TOKEN_TIMEOUT_SECONDS,
        refresh_lifetime = settings.OAUTH2_REFRESH_TOKEN_TIMEOUT_SECONDS,
        **data)
    return JSONResponse(token.dict(model=TokenResponse))


@_app.validate(json=None,
               resp=Response(HTTP_201=TokenResponse,
                             HTTP_403=None,
                             HTTP_409=ValidationErrorList,
                             HTTP_422=ValidationErrorList), tags=['tokens'])
async def token(request):
    data = TokenRequest(**dict(await request.form())).dict()
    try:
        token = OAuth2Token.objects.create(
            access_lifetime = settings.OAUTH2_ACCESS_TOKEN_TIMEOUT_SECONDS,
            refresh_lifetime = settings.OAUTH2_REFRESH_TOKEN_TIMEOUT_SECONDS,
            **data)
    except (OAuth2Client.DoesNotExist, OAuth2Client.InvalidOAuth2Client,
            OAuth2Token.InvalidGrantType) as e:
        return JSONResponse({ 'message': str(e) }, status_code=403)
    return JSONResponse(token.dict(model=TokenResponse))

