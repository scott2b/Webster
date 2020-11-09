from spectree import Response
from starlette.responses import JSONResponse
from ...config import settings
from ...orm.oauth2.client import OAuth2Client
from ...orm.oauth2.token import OAuth2Token
from ...schemas.oauth2token import TokenResponse, TokenCreateRequest, TokenRefreshRequest
from . import _app, ValidationErrorList, APIExceptionResponse


# OAuth2 spec seems to mandate form data (not json) for a token request:
# https://github.com/requests/requests-oauthlib/issues/244

@_app.validate(json=None,
               resp=Response(HTTP_201=TokenResponse,
                             HTTP_401=APIExceptionResponse,
                             HTTP_403=APIExceptionResponse,
                             HTTP_409=ValidationErrorList,
                             HTTP_422=ValidationErrorList), tags=['tokens'])
async def token_refresh(request):
    data = dict(await request.form())
    obj = TokenRefreshRequest(
        access_lifetime = settings.OAUTH2_ACCESS_TOKEN_TIMEOUT_SECONDS,
        refresh_lifetime = settings.OAUTH2_REFRESH_TOKEN_TIMEOUT_SECONDS,
        **data)
    try:
        token = OAuth2Token.objects.refresh(obj)
    except OAuth2Token.DoesNotExist:
        raise HTTPException(404, "Not found")
    except OAuth2Token.Revoked:
        raise HTTPException(401, "Invalid token")
    except OAuth2Token.Expired:
        raise HTTPException(403, "Expired token")
    return JSONResponse(token.dict(model=TokenResponse))


@_app.validate(json=None,
               resp=Response(HTTP_201=TokenResponse,
                             HTTP_401=APIExceptionResponse,
                             HTTP_403=APIExceptionResponse,
                             HTTP_409=ValidationErrorList,
                             HTTP_422=ValidationErrorList), tags=['tokens'])
async def token_create(request):
    data = dict(await request.form())
    try:
        obj = TokenCreateRequest(
            access_lifetime = settings.OAUTH2_ACCESS_TOKEN_TIMEOUT_SECONDS,
            refresh_lifetime = settings.OAUTH2_REFRESH_TOKEN_TIMEOUT_SECONDS,
            scope='api', **data)
        token = OAuth2Token.objects.create(obj)
    except (OAuth2Client.DoesNotExist, OAuth2Client.InvalidOAuth2Client):
        raise HTTPException(401, "Unauthorized")
    except OAuth2Token.InvalidGrantType:
        raise HTTPException(403, "Invalid grant type")
    return JSONResponse(token.dict(model=TokenResponse), status_code=201)

