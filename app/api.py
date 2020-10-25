import datetime
from pydantic import BaseModel, Field, constr
from spectree import SpecTree, Response
from spectree.plugins.starlette_plugin import StarlettePlugin, PAGES
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from . import orm

#from .orm.models import OAuth2Client, OAuth2Token
#from .orm.models.oauth2 import create_key, ACCESS_TOKEN_BYTES, REFRESH_TOKEN_BYTES
#from .orm import SessionLocal

#from dependency_injector.wiring import Provide
#from sqlalchemy.orm.session import Session
#from .containers import Container


UI_ROUTES = {
  'redoc': 'api',
  'swagger': 'swagger'
}

class CustomPlugin(StarlettePlugin):

    def register_route(self, app):
        self.app = app
        try:
            self.app.add_route(
                self.config.spec_url,
                lambda request: JSONResponse(self.spectree.spec),
            )
        except: # wtf?
            pass
        for ui in PAGES:
            self.app.add_route(
                f'/{self.config.PATH}/{UI_ROUTES[ui]}',
                lambda request, ui=ui: HTMLResponse(
                    PAGES[ui].format(self.config.spec_url)
                ),
            )

api = SpecTree('starlette', path='docs', backend=CustomPlugin, MODE='strict')
# api = SpecTree('starlette', path='docs', MODE='strict')


class Message(BaseModel):
    text: str


class Profile(BaseModel):
    name: constr(min_length=2, max_length=40)  # Constrained Str
    age: int = Field(
        ...,
        gt=0,
        lt=150,
        description='user age(Human)'
    )


@api.validate(json=Profile, resp=Response(HTTP_200=Message, HTTP_403=None), tags=['api'])
@requires('app_auth', status_code=403)
async def user_profile(request):
    """
    verify user profile (summary of this endpoint)

    user's name, user's age, ... (long description)
    """
    print(request.context.json)  # or await request.json()
    return JSONResponse({'text': 'it works'})


@requires(['api_auth'], status_code=403)
def widget(request):
    print(request.scope)
    print(dir(request.auth))
    print(request.auth.scopes)
    return JSONResponse({ 'foo': 'bar' })



"""
Headers({'host': 'localhost:8000', 'user-agent': 'python-requests/2.24.0', 'accept-encoding': 'gzip, deflate', 'accept': '*/*', 'connection': 'keep-alive', 'authorization': 'OAuth oauth_nonce="o8UwM6s2yCqZKjt5lhDMKhg0Uqk8Kw", oauth_timestamp="1603486212", oauth_version="1.0", oauth_signature_method="HMAC-SHA1", oauth_consumer_key="YOUR-CLIENT-ID", oauth_token="oauth_token", oauth_signature="PRtLO8T8l2HyccoIeGGx40O1Tcs%3D"'})
"""

def authorize(request):
    print(request.headers)
    #grant = server.validate_consent_request(request, end_user=request.user)
    #context = dict(grant=grant, user=request.user)
    #return render(request, 'authorize.html', context)
    #if is_user_confirmed(request):
    #    # granted by resource owner
    #    return server.create_authorization_response(request, grant_user=request.user)
    ## denied by resource owner
    #return server.create_authorization_response(request, grant_user=None)


import secrets

_token = {
    'access_token': secrets.token_urlsafe(32),
    'refresh_token': secrets.token_urlsafe(128),
    'token_type': 'Bearer',
}


def get_token():
    global _token
    return _token


def set_token(t):
    global _token
    _token = t




#async def token_refresh(request, db:Session=Provide[Container.database_client]):
async def token_refresh(request):
    print('REFRESH TOKEN REQUEST AT:', datetime.datetime.utcnow())
    print('HEADERS', request.headers)
    data = await request.form()
    #db = SessionLocal()
    #token = orm.models.oauth2.OAuth2Token.refresh(db, data['grant_type'], data['refresh_token'], 30, 60)
    #token = orm.models.oauth2.OAuth2Token.refresh(data['grant_type'], data['refresh_token'], 30, 60)
    token = orm.oauth2.oauth2_tokens.refresh(data['grant_type'], data['refresh_token'], 30, 60)
    return JSONResponse(token.response_data())


#async def token(request, db:Session=Provide[Container.database_client]):
async def token(request):
    print('TOKEN REQUEST AT:', datetime.datetime.utcnow())
    data = await request.form()
    print(data)
    #db = SessionLocal()
    access_lifetime = 30
    refresh_lifetime = 60
    #token = orm.oauth2.OAuth2Token.create(data['grant_type'], data['client_id'], data['client_secret'], access_lifetime, refresh_lifetime)
    token = orm.oauth2.oauth2_tokens.create(data['grant_type'], data['client_id'], data['client_secret'], access_lifetime, refresh_lifetime)
    if token:
        return JSONResponse(token.response_data())


routes = [
    Route('/user', user_profile, methods=['POST']),
    Route('/auth', authorize, methods=['GET']),
    Route('/token', token, methods=['POST']),
    Route('/token-refresh', token_refresh, methods=['POST']),
    Route('/widget/', widget)
]

app = Starlette(
    debug=True,
    routes=routes,
    on_startup=[])


api.register(app)
