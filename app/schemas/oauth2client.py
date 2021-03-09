"""
Schema for OAuth2 application client
"""
import datetime
from typing import List, Optional
from pydantic import BaseModel, validator


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
