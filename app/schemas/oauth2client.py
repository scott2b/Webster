"""
Schema for OAuth2 application client
"""
import datetime
from typing import List, Optional
from pydantic import BaseModel, validator
from ..orm.user import User
from ..auth import create_random_key
from ..orm import OAUTH2_CLIENT_ID_BYTES, OAUTH2_CLIENT_SECRET_BYTES


class OAuth2ClientBase(BaseModel):
    """OAuth2 API client base validator."""

    class Config:
        """Config OAuth2ClientBase."""
        arbitrary_types_allowed = True

    id: Optional[int]
    name: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    created_at: Optional[datetime.datetime]
    secret_expires_at: Optional[datetime.datetime]
    user: Optional[User]


class OAuth2ClientUpdate(OAuth2ClientBase):
    """OAuth2 API client update name."""
    name: str


class OAuth2ClientRequest(BaseModel):
    """Client request schema"""
    name: str


class OAuth2ClientResponse(BaseModel):
    """Client response schema"""

    class Config:
        """Configure TokenCreate"""
        extra = 'ignore'

    name: str
    created_at: datetime.datetime
    client_id: str
    client_secret: str
    secret_expires_at: Optional[datetime.datetime]

    @validator('created_at')
    @classmethod
    def serialize_created_at(cls, v):
        """Convert the created_at field to a string."""
        if v:
            return v.isoformat()
        return None

    @validator('secret_expires_at')
    @classmethod
    def serialize_secret_expires_at(cls, v):
        """Convert the secret_expires_at field to a string."""
        if v:
            return v.isoformat()
        return None


class OAuth2ClientListResponse(BaseModel):
    """Client list schema"""
    clients: List[OAuth2ClientResponse]
