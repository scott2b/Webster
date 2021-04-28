import copy
import datetime
from starlette.authentication import AuthenticationBackend, AuthCredentials
from ..orm import oauth2token
from ..orm.user import User


class SessionAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        if 'user_id' in request.session:
            user_id = request.session['user_id']
            user = User.objects.get(user_id)
            creds = ['app_auth']
            if user.is_superuser:
                creds.append('admin_auth')
            if user.user_data and 'asUser' in user.user_data:
                if request.url.path == '/auth/logout':
                    data = copy.copy(user.user_data)
                    del data['asUser']
                    user.user_data = data
                    user.save() 
                else:
                    spoof_user = User.objects.get_by_email(user.user_data['asUser'])
                    return AuthCredentials(creds), spoof_user
            return AuthCredentials(creds), user
        if request.headers.get('authorization'):
            bearer = request.headers['authorization'].split()
            if bearer[0] != 'Bearer':
                return
            bearer = bearer[1]
            token = oauth2token.OAuth2Token.objects.get_by_access_token(bearer)
            if token is None or token.revoked:
                return # return without authorization
            if datetime.datetime.utcnow() > token.access_token_expires_at:
                return # return without authorization
            # passed all tests
            request.scope['token'] = token
            return AuthCredentials(['api_auth']), None
