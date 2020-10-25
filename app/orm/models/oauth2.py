"""
https://docs.authlib.org/en/latest/flask/2/authorization-server.html
"""
from __future__ import annotations # for returning self type from classmethod. remove in Py3.10
import datetime
import secrets
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship, Session
from ..base import Base
from .user import User


"""
The secrets module gives Base64 encoded text which is ~1.3 characters per byte.

For details on use of the secrets module for cryptographic key generation see:
https://docs.python.org/3/library/secrets.html
"""
CLIENT_ID_BYTES = 32
CLIENT_SECRET_BYTES = 64
ACCESS_TOKEN_BYTES = 32
REFRESH_TOKEN_BYTES = 64

CLIENT_ID_MAX_CHARS = int(CLIENT_ID_BYTES * 1.5)
CLIENT_SECRET_MAX_CHARS = int(CLIENT_SECRET_BYTES * 1.5)
ACCESS_TOKEN_MAX_CHARS = int(ACCESS_TOKEN_BYTES * 1.5)
REFRESH_TOKEN_MAX_CHARS = int(REFRESH_TOKEN_BYTES * 1.5)


def create_key(nbytes):
    return secrets.token_urlsafe(nbytes)



class OAuth2Client(Base):

    __tablename__ = 'oauth2_clients'

    id = Column(Integer, primary_key=True)
    client_id = Column(String(CLIENT_ID_MAX_CHARS), unique=True, index=True, nullable=False)
    client_secret = Column(String(CLIENT_SECRET_MAX_CHARS), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    secret_expires_at = Column(Integer, nullable=True)
    user_id = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE')
    )
    user = relationship('User')

    @classmethod
    def create_for_user(cls, db: Session, user:User) -> OAuth2Client:
        db_obj = OAuth2Client(
            client_id=create_key(CLIENT_ID_BYTES),
            client_secret=create_key(CLIENT_SECRET_BYTES),
            user=user
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @classmethod
    def get_by_client_id(cls, db: Session, client_id: str) -> Optional[OAuth2Client]:
        return db.query(OAuth2Client).filter(OAuth2Client.client_id == client_id).first()


class OAuth2Token(Base):

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

    @classmethod
    def get_by_access_token(cls, db: Session, access_token: str) -> Optional[OAuth2Token]:
        return db.query(OAuth2Token).filter(OAuth2Token.access_token == access_token).first()

    @classmethod
    def get_by_refresh_token(cls, db: Session, refresh_token: str) -> Optional[OAuth2Token]:
        return db.query(OAuth2Token).filter(OAuth2Token.refresh_token == refresh_token).first()

    @classmethod
    def create(cls, db:Session, grant_type:str, client_id:str, client_secret:str, access_lifetime:int, refresh_lifetime:int) -> Optional[OAuth2Token]:
        """
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
            raise Exception
        client = OAuth2Client.get_by_client_id(db, client_id)
        valid = secrets.compare_digest(client_secret, client.client_secret)
        if not valid:
            raise Exception
        access_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=access_lifetime) 
        print('ACCESS EXPIRES', access_expires)
        refresh_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=refresh_lifetime) 
        print('REFRESH EXPIRES', refresh_expires)
        db_obj = OAuth2Token(
            client=client,
            token_type='Bearer',
            access_token=create_key(ACCESS_TOKEN_BYTES),
            refresh_token=create_key(REFRESH_TOKEN_BYTES),
            access_token_expires_at=access_expires,
            refresh_token_expires_at=refresh_expires

        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        print('CREATED TOKEN WITH')
        print('ACCESS EXPIRES:', db_obj.access_token_expires_at)
        print('REFRESH EXPIRES:', db_obj.refresh_token_expires_at)
        return db_obj

    def response_data(self):
        now = datetime.datetime.utcnow()
        expires_in = (self.access_token_expires_at - now).seconds
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_in': expires_in
        }

    @classmethod
    def refresh(cls, db:Session, grant_type:str, refresh_token:str, access_lifetime:int, refresh_lifetime:int) -> Optional[OAuth2Token]:
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
        token = cls.get_by_refresh_token(db, refresh_token)
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
        db.commit()
        db.refresh(token)
        print('REFRESHED TOKEN WITH')
        print('ACCESS EXPIRES', token.access_token_expires_at)
        print('REFRESH EXPIRES', token.refresh_token_expires_at)
        return token
