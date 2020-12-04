"""
Schema for OAuth2 tokens
"""
import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, validator
from ..orm.oauth2client import OAuth2Client
from ..auth import create_random_key
from ..orm import OAUTH2_ACCESS_TOKEN_BYTES, OAUTH2_REFRESH_TOKEN_BYTES


class GrantTypes(str, Enum):
    """Valid grant types"""
    client_credentials = 'client_credentials'
    refresh_token = 'refresh_token'


class OAuth2TokenCreate(BaseModel):
    """Token creation schema"""

    class Config:
        """Configure TokenCreate"""
        arbitrary_types_allowed = True
        extra = 'ignore'

    client: OAuth2Client
    token_type: str
    access_token: str
    refresh_token: str
    scope: str
    revoked: bool = False
    access_token_expires_at: datetime.datetime
    refresh_token_expires_at: datetime.datetime


class _TokenRequest(BaseModel):
    """Base validation and token generation for new-token and refresh-token
    requests.
    """
    grant_type: Optional[GrantTypes]
    token_type: Optional[str]  = 'Bearer'
    client_id: Optional[str]
    client_secret: Optional[str]
    access_token: Optional[str]
    refresh_token: Optional[str]
    scope: Optional[str]
    access_lifetime: Optional[int]
    refresh_lifetime: Optional[int]
    access_token_expires_at: Optional[datetime.datetime]
    refresh_token_expires_at: Optional[datetime.datetime]

    @validator('access_token_expires_at', always=True)
    @classmethod
    def set_access_token_expires_at(cls, v, values):
        """Set the access token expire"""
        if not v and 'access_lifetime' in values:
            delta = values['access_lifetime']
            v = datetime.datetime.utcnow() \
                + datetime.timedelta(seconds=delta)
            del values['access_lifetime']
        return v

    @validator('refresh_token_expires_at', always=True)
    @classmethod
    def set_refresh_token_expires_at(cls, v, values):
        """Set the token expire"""
        if not v and 'refresh_lifetime' in values:
            delta = values['refresh_lifetime']
            v = datetime.datetime.utcnow() \
                + datetime.timedelta(seconds=delta)
            del values['refresh_lifetime']
        return v

    @validator('access_token', always=True)
    @classmethod
    def generate_access_token(cls, v):
        """Generate the access token"""
        if not v:
            v = create_random_key(OAUTH2_ACCESS_TOKEN_BYTES)
        return v

    @validator('refresh_token', always=True)
    @classmethod
    def generate_refresh_token(cls, v):
        """Generate the refresh token"""
        if not v:
            v = create_random_key(OAUTH2_REFRESH_TOKEN_BYTES)
        return v


class TokenCreateRequest(_TokenRequest):
    """Validate a request for a new token request from the API. Generates and
    sets the token values.
    """
    grant_type: GrantTypes
    token_type: str  = 'Bearer'
    client_id: str
    client_secret: str
    access_token: Optional[str]
    refresh_token: Optional[str]
    scope: str
    access_lifetime: int
    refresh_lifetime: int
    access_token_expires_at: Optional[datetime.datetime]
    refresh_token_expires_at: Optional[datetime.datetime]

    @validator('grant_type')
    @classmethod
    def check_grant_type(cls, v, values):
        """Check for valid grant type"""
        if v == GrantTypes.client_credentials:
            return v
        raise ValueError('Invalid Grant Type')


class TokenRefreshRequest(_TokenRequest):
    """Validate token refresh request."""
    grant_type: GrantTypes
    refresh_token: str

    class Config:
        """Configure TokenRefreshRequest."""
        extra = 'ignore'

    @validator('grant_type')
    @classmethod
    def check_grant_type(cls, v):
        """Check for valid grant type"""
        if v == GrantTypes.refresh_token:
            return v
        raise ValueError('Invalid Grant Type')


class TokenResponse(BaseModel):
    """client_credentials granted access token of Bearer type."""
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
                raise ValueError(
                    'Either expires_in or access_token_expires_at required.')
        return v


class ScopedTokenResponse(TokenResponse):
    """
    Scope of response is required if granted scope is different from
    requested scope.

    Not really needed for client_credentials, which is all we are supporting
    at the moment.
    """
    scope: str
