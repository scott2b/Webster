"""
https://docs.authlib.org/en/latest/flask/2/authorization-server.html
"""
#from __future__ import annotations # for returning self type from classmethod. remove in Py3.10
import datetime
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, validator, ValidationError # pylint:disable=no-name-in-module
from dependency_injector.wiring import Provide, Closing
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship, Session
from .. import base
from ...containers import Container
from .client import oauth2_clients, create_key, OAuth2Client
from . import (
    ACCESS_TOKEN_BYTES,
    REFRESH_TOKEN_BYTES,
    ACCESS_TOKEN_MAX_CHARS,
    REFRESH_TOKEN_MAX_CHARS
)


class InvalidGrantType(Exception):
    """Invalid token auth grant-type."""


class Revoked(Exception):
    """Reoved token."""


class Expired(Exception):
    """Expired token."""


### Schema

class TokenRequest(BaseModel):
    """Validate a request for a new token."""
    # pylint: disable=too-few-public-methods
    grant_type:str
    client_id:str
    client_secret:str


class TokenRefreshRequest(BaseModel):
    """Validate token refresh request."""
    # pylint: disable=too-few-public-methods

    class Config:
        """Configure TokenRefreshRequest."""
        extra = 'ignore'

    grant_type: str
    refresh_token: str


class TokenResponse(BaseModel):
    """client_credentials granted access token of Bearer type."""
    # pylint: disable=too-few-public-methods
    access_token: str
    token_type: str
    refresh_token: str
    access_token_expires_at: Optional[datetime.datetime]
    expires_in: Optional[int]

    @validator('expires_in', always=True)
    @classmethod
    def set_expires_in(cls, v, values):
        """Set the expires_in value based on the access_token_expires_at value.
        """
        if not v:
            if 'access_token_expires_at' in values:
                now = datetime.datetime.utcnow()
                v = (values['access_token_expires_at'] - now).seconds
                del values['access_token_expires_at']
            else:
                raise ValidationError(
                    'Either expires_in or access_token_expires_at required.')
        return v


class ScopedTokenResponse(TokenResponse):
    """
    Scope of response is required if granted scope is different from
    requested scope.

    Not really needed for client_credentials, which is all we are supporting
    at the moment.
    """
    # pylint: disable=too-few-public-methods
    scope: str



### ORM

@dataclass
class OAuth2Token(base.ModelBase, base.DataModel):
    """OAuth2 token model with access and refresh data."""
    # pylint: disable=too-few-public-methods

    __tablename__ = 'oauth2_tokens'

    id:int = Column(Integer, primary_key=True)
    client_id:int = Column(
        Integer, ForeignKey('oauth2_clients.id', ondelete='CASCADE')
    )
    token_type:str = Column(String(40))
    access_token:str = Column(String(ACCESS_TOKEN_MAX_CHARS), index=True,
                          unique=True, nullable=False)
    refresh_token:str = Column(String(REFRESH_TOKEN_MAX_CHARS), index=True,
                           unique=True)
    scope:str = Column(Text, default='')
    revoked:bool = Column(Boolean, default=False)
    created_at:datetime.datetime = Column(DateTime, nullable=False,
                        default=datetime.datetime.utcnow)
    refreshed_at:datetime.datetime = Column(DateTime, nullable=False,
                          default=datetime.datetime.utcnow)
    access_token_expires_at:datetime.datetime = Column(DateTime, nullable=False)
    refresh_token_expires_at:datetime.datetime = Column(DateTime)
    client = relationship('OAuth2Client') # type: ignore

    InvalidGrantType = InvalidGrantType # pylint:disable=invalid-name
    Revoked = Revoked # pylint:disable=invalid-name
    Expired = Expired # pylint:disable=invalid-name

    def get_user(self, db:Session=Closing[Provide[Container.closed_db]]):
        """Get the user associated with this token."""
        return db.query(OAuth2Client).filter(
            OAuth2Client.id == self.client_id).first().user


class OAuth2TokenManager():
    """OAuth2 Token object manager."""

    @classmethod
    def get_by_access_token(cls, access_token: str, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> Optional[OAuth2Token]:
        """Get a token by the access token string."""
        return db.query(OAuth2Token).filter(
            OAuth2Token.access_token == access_token).first()

    @classmethod
    def get_by_refresh_token(cls, refresh_token: str, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> Optional[OAuth2Token]:
        """Get a token by the refresh token string."""
        return db.query(OAuth2Token).filter(
            OAuth2Token.refresh_token == refresh_token).first()

    @classmethod
    def create(cls, *,
            grant_type:str,
            client_id:str,
            client_secret:str,
            access_lifetime:int,
            refresh_lifetime:int,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> OAuth2Token:
        """
        Create a new token for the given data.

        Currently only supporting creation of client_credentials granted tokens
        and bearer token type:
        https://www.oauth.com/oauth2-servers/access-tokens/client-credentials/

        grant_type: must be client_credentials
        scope (optional): scope of requested access, not really necessary for
                          client_credentials
        client authentication: client_id, client_secret (additional request
                               parameters, or in header)

        Should generate an access token response:
        https://www.oauth.com/oauth2-servers/access-tokens/access-token-response/

         * access_token (required)
         * token_type (required), typically "bearer"
         * expires_in (recommended)
         * refresh_token (optional) (not valid for implicit grant)
         * scope (optional) required if granted scope is different from
           requested scope

        Also include:
            * Cache-Control: no-store
            * Pragma: no-cache

        in the response headers

        Access token format (https://tools.ietf.org/html/rfc6750)

         * alpha-numeric and -._~+/ characters

        Either:
            * generate a random string
            * or, use self-encoded tokens (
              https://www.oauth.com/oauth2-servers/access-tokens/self-encoded-access-tokens/)

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
            raise OAuth2Token.InvalidGrantType
        client = oauth2_clients.get_by_client_id(client_id, db=db)
        if not client:
            raise OAuth2Client.DoesNotExist
        if not client.compare_secret(client_secret):
            raise OAuth2Client.InvalidOAuth2Client
        access_expires = datetime.datetime.utcnow() \
            + datetime.timedelta(seconds=access_lifetime)
        refresh_expires = datetime.datetime.utcnow() \
            + datetime.timedelta(seconds=refresh_lifetime)
        token = OAuth2Token(
            client=client,
            token_type='Bearer',
            access_token=create_key(ACCESS_TOKEN_BYTES),
            refresh_token=create_key(REFRESH_TOKEN_BYTES),
            access_token_expires_at=access_expires,
            refresh_token_expires_at=refresh_expires

        )
        db.add(token)
        return token

    @classmethod
    def refresh(cls, *,
            grant_type:str,
            refresh_token:str,
            access_lifetime:int,
            refresh_lifetime:int,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> OAuth2Token:
        """
        https://www.oauth.com/oauth2-servers/access-tokens/refreshing-access-tokens/

        Refresh the token.

        TODO: implement refresh

        e.g. refresh for:
        FORM DATA FormData([
            ('grant_type', 'refresh_token'),
            ('refresh_token', '__k85z_6A-QLV5tZLO2s ... ')])

        grant_type: must be "refresh_token"
        refresh_token: must match the stored refresh token
        scope (optional): must not include additional scopes from original
                          access token
        client authentication (required if client was issued a secret):
            client_id and client_secret???

        After checking for all required parameters, and authenticating the
        client if the client was issued a secret:

        * refresh token is valid
        * refresh token not expired
        * generate a new access token (may also include a new refresh token)

        ? is requests including client_id & secret in refresh requests?
        NO DOES NOT SEEM TO
        """
        if grant_type != 'refresh_token':
            raise OAuth2Token.InvalidGrantType
        token = cls.get_by_refresh_token(refresh_token, db=db)
        # TODO: ensure scope request is not expanded
        # TODO: do we need to check client auth? requests does not include
        #       client_id or secret in a refresh request
        if not token:
            raise OAuth2Token.DoesNotExist
        if token.revoked:
            raise OAuth2Token.Revoked
        if datetime.datetime.now() > token.refresh_token_expires_at:
            raise OAuth2Token.Expired
        token.access_token = create_key(ACCESS_TOKEN_BYTES)
        token.refresh_token = create_key(REFRESH_TOKEN_BYTES)
        now = datetime.datetime.utcnow()
        token.access_token_expires_at = now \
            + datetime.timedelta(seconds=access_lifetime)
        token.refresh_token_expires_at = now \
            + datetime.timedelta(seconds=refresh_lifetime)
        db.add(token)
        return token

oauth2_tokens = OAuth2TokenManager()
OAuth2Token.objects = oauth2_tokens
