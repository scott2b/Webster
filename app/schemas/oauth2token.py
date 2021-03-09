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


class NewTokenRequest(BaseModel):
    grant_type: GrantTypes
    token_type: Optional[str]  = 'Bearer'
    client_id: str
    client_secret: str


class TokenRefreshRequest(BaseModel):
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
