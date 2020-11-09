import datetime
from pydantic import BaseModel, validator
from typing import List, Optional
from ..orm.user import User
from ..auth.security import create_random_key
from ..orm.oauth2 import CLIENT_ID_BYTES, CLIENT_SECRET_BYTES

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


class OAuth2ClientCreate(OAuth2ClientBase):
    """OAuth2 API client create validator."""

    name: str
    user: User
    client_id: Optional[str]
    client_secret: Optional[str]

    @validator('client_id', always=True)
    @classmethod
    def generate_client_id(cls, v):
        """Generate the client ID."""
        return create_random_key(CLIENT_ID_BYTES)

    @validator('client_secret', always=True)
    @classmethod
    def generate_client_secret(cls, v):
        """Generate the client secret."""
        return create_random_key(CLIENT_SECRET_BYTES)


class OAuth2ClientUpdate(OAuth2ClientBase):
    """OAuth2 API client update name."""
    name: str


    
class OAuth2ClientRequest(BaseModel):
    name: str


class OAuth2ClientResponse(BaseModel):

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
    
    @validator('secret_expires_at')
    @classmethod
    def serialize_secret_expires_at(cls, v):
        """Convert the secret_expires_at field to a string."""
        if v:
            return v.isoformat()

class OAuth2ClientListResponse(BaseModel):
    clients: List[OAuth2ClientResponse]


