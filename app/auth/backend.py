from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser
from dependency_injector.wiring import Provide
from sqlalchemy.orm.session import Session
from ..containers import Container
from .. import orm

import datetime

class SessionAuthBackend(AuthenticationBackend):

    async def authenticate(self, request, db:Session=Provide[Container.database_client]):
        print('INJECTED', db)
        print('SCOPE', request.scope)
        print('---')
        if 'username' in request.session:
            username = request.session['username']
            return AuthCredentials(['app_auth', 'api_auth']), SimpleUser(username)
        if request.headers.get('authorization'):
            bearer = request.headers['authorization'].split()
            if bearer[0] != 'Bearer':
                return
            bearer = bearer[1]
            #db = orm.SessionLocal()
            print('TYPED', type(db))
            token = orm.models.OAuth2Token.get_by_access_token(db, bearer)
            if token.revoked:
                raise Exception
            if datetime.datetime.utcnow() > token.access_token_expires_at:
                raise Exception
            return AuthCredentials(['api_auth']), None
