"""
https://docs.authlib.org/en/latest/flask/2/authorization-server.html
"""
#from __future__ import annotations # for returning self type from classmethod. remove in Py3.10
import datetime
import secrets
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship, Session
from .. import base, user

from dependency_injector.wiring import Provide
from ...containers import Container

from . import (
    ACCESS_TOKEN_BYTES,
    REFRESH_TOKEN_BYTES,
    ACCESS_TOKEN_MAX_CHARS,
    REFRESH_TOKEN_MAX_CHARS
)


from .client import oauth2_clients, create_key


class OAuth2Token(base.Base):

    __tablename__ = 'oauth2_tokens'

    id = Column(Integer, primary_key=True)
    client_id = Column(
        Integer, ForeignKey('oauth2_clients.id', ondelete='CASCADE')
    )
    token_type = Column(String(40))
    access_token = Column(String(ACCESS_TOKEN_MAX_CHARS), index=True, unique=True, nullable=False)
    refresh_token = Column(String(REFRESH_TOKEN_MAX_CHARS), index=True, unique=True)
    scope = Column(Text, default='')
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    refreshed_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    access_token_expires_at = Column(DateTime, nullable=False)
    refresh_token_expires_at = Column(DateTime)
    client = relationship('OAuth2Client')

    def response_data(self):
        now = datetime.datetime.utcnow()
        expires_in = (self.access_token_expires_at - now).seconds
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_in': expires_in
        }


class OAuth2TokenManager():

    def get_by_access_token(cls, access_token: str, db:Session=Provide[Container.db]):
        return db.query(OAuth2Token).filter(OAuth2Token.access_token == access_token).first()

    def get_by_refresh_token(cls, refresh_token: str, db:Session=Provide[Container.db]):
        return db.query(OAuth2Token).filter(OAuth2Token.refresh_token == refresh_token).first()

    def create(
            cls,
            grant_type:str,
            client_id:str,
            client_secret:str,
            access_lifetime:int,
            refresh_lifetime:int,
            db:Session=Provide[Container.db],
            commit=True,
            **kwargs):
        """
        Create a new token for the given data. Commits unless specified False.

        Currently only supporting creation of client_credentials granted tokens
        and bearer token type:
        https://www.oauth.com/oauth2-servers/access-tokens/client-credentials/

        grant_type: must be client_credentials
        scope (optional): scope of requested access, not really necessary for client_credentials
        client authentication: client_id, client_secret (additional request parameters, or in header)

        Should generate an access token response:
        https://www.oauth.com/oauth2-servers/access-tokens/access-token-response/

         * access_token (required)
         * token_type (required), typically "bearer"
         * expires_in (recommended)
         * refresh_token (optional) (not valid for implicit grant)
         * scope (optional) required if granted scope is different from requested scope

        Also include:
            * Cache-Control: no-store
            * Pragma: no-cache

        in the response headers

        Access token format (https://tools.ietf.org/html/rfc6750)

         * alpha-numeric and -._~+/ characters

        Either:
            * generate a random string
            * or, use self-encoded tokens (https://www.oauth.com/oauth2-servers/access-tokens/self-encoded-access-tokens/)

        Invalid request:
            * invalid_request (400 for this one and generally)
            * invalid_client (401 for this one)
            * invalid_grant
            * invalid_scope
            * unauthorized_client
            * unsupported_grant_type

        Also, optional parameters:
            * error_description (ascii only - a sentence or 2)
            * error_uri - link, e.g. to api docs
        """
        if grant_type != 'client_credentials':
            raise Exception('Invalid grant type')
        client = oauth2_clients.get_by_client_id(client_id, db=db)
        valid = secrets.compare_digest(client_secret, client.client_secret)
        if not valid:
            raise Exception('Invalid client')
        access_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=access_lifetime) 
        refresh_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=refresh_lifetime) 
        token = OAuth2Token(
            client=client,
            token_type='Bearer',
            access_token=create_key(ACCESS_TOKEN_BYTES),
            refresh_token=create_key(REFRESH_TOKEN_BYTES),
            access_token_expires_at=access_expires,
            refresh_token_expires_at=refresh_expires

        )
        db.add(token)
        if commit:
            db.commit()
        return token

    def refresh(cls,
            grant_type:str,
            refresh_token:str,
            access_lifetime:int,
            refresh_lifetime:int,
            db:Session=Provide[Container.db],
            commit=True,
            **kwargs):
        """
        https://www.oauth.com/oauth2-servers/access-tokens/refreshing-access-tokens/

        TODO: implement refresh

        e.g. refresh for:
        FORM DATA FormData([
            ('grant_type', 'refresh_token'),
            ('refresh_token', '__k85z_6A-QLV5tZLO2snaY59GEbmwxqsYBJGhHgnWcmXvR0-_OOwaEOu1Smnk51KXQo3GzVwlszH3ISBMGUog')])

        grant_type: must be "refresh_token"
        refresh_token: must match the stored refresh token
        scope (optional): must not include additional scopes from original access token
        client authentication (required if client was issued a secret): client_id and client_secret???

        After checking for all required parameters, and authenticating the client if the client was issued a secret:

        * refresh token is valid
        * refresh token not expired
        * generate a new access token (may also include a new refresh token)

        ? is requests including client_id & secret in refresh requests? NO DOES NOT SEEM TO
        """
        if grant_type != 'refresh_token':
            raise Exception
        token = cls.get_by_refresh_token(refresh_token, db=db)
        # TODO: ensure scope request is not expanded
        # TODO: do we need to check client auth? requests does not include client_id or secret in a refresh request
        if token.revoked:
            raise Exception
        if datetime.datetime.now() > token.refresh_token_expires_at:
            raise Exception('Refresh token expired:',
                (token.refresh_token_expires_at - datetime.datetime.utcnow()).seconds)
        token.access_token = create_key(ACCESS_TOKEN_BYTES)
        token.refresh_token = create_key(REFRESH_TOKEN_BYTES)
        now = datetime.datetime.utcnow()
        token.access_token_expires_at = now + datetime.timedelta(seconds=access_lifetime) 
        token.refresh_token_expires_at = now + datetime.timedelta(seconds=refresh_lifetime) 
        db.add(token)
        if commit:
            db.commit()
        return token

oauth2_tokens = OAuth2TokenManager()
