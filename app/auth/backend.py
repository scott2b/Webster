import datetime
from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser
from .. import orm
from ..orm.session import session_scope as db_session_scope
from ..orm.oauth2 import oauth2_tokens


class SessionAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        if 'username' in request.session:
            username = request.session['username']
            return AuthCredentials(['app_auth', 'api_auth']), SimpleUser(username)
        if request.headers.get('authorization'):
            bearer = request.headers['authorization'].split()
            if bearer[0] != 'Bearer':
                return
            bearer = bearer[1]
            with db_session_scope() as db:
                token = oauth2_tokens.get_by_access_token(db, bearer)
                if token.revoked:
                    raise Exception
                if datetime.datetime.utcnow() > token.access_token_expires_at:
                    raise Exception
            return AuthCredentials(['api_auth']), None
