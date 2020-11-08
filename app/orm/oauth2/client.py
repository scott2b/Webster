"""
https://docs.authlib.org/en/latest/flask/2/authorization-server.html
"""
import datetime
import secrets
from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel, validator
from dependency_injector.wiring import Provide, Closing
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship, Session
from sqlalchemy import UniqueConstraint
from .. import base
from ..user import User
from ...containers import Container
from . import (
    CLIENT_ID_BYTES,
    CLIENT_SECRET_BYTES,
    CLIENT_ID_MAX_CHARS,
    CLIENT_SECRET_MAX_CHARS
)


def create_key(nbytes):
    """Create a URL safe secret token."""
    return secrets.token_urlsafe(nbytes)


### Schema

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
        return create_key(CLIENT_ID_BYTES)

    @validator('client_secret', always=True)
    @classmethod
    def generate_client_secret(cls, v):
        """Generate the client secret."""
        return create_key(CLIENT_SECRET_BYTES)


class OAuth2ClientUpdate(OAuth2ClientBase):
    """OAuth2 API client update name."""
    name: str


class InvalidOAuth2Client(Exception):
    """Invalid OAuth2 client."""

    
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



### ORM

@dataclass
class OAuth2Client(base.ModelBase, base.DataModel):
    """OAuth2 API Client model.

    TODO: user should be non-nullable
    """
    # pylint: disable=too-few-public-methods

    __tablename__ = 'oauth2_clients'
    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='name_user_id_unique_1'),
    )

    id:int = Column(Integer, primary_key=True)
    name:str = Column(String(100), nullable=False, default='Primary')
    client_id:str = Column(String(CLIENT_ID_MAX_CHARS), unique=True,
        index=True, nullable=False)
    client_secret:str = Column(String(CLIENT_SECRET_MAX_CHARS), unique=True,
        index=True, nullable=False)
    created_at:datetime.datetime = Column(DateTime, nullable=False,
        default=datetime.datetime.utcnow)
    secret_expires_at:datetime.datetime = Column(Integer, nullable=True)
    user_id:int = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE')
    )
    user = relationship('User') # type: ignore

    InvalidOAuth2Client = InvalidOAuth2Client

    def compare_secret(self, secret):
        """Compare a given secret with the secret for this instance.

        Returns True if they are the same.
        """
        return secrets.compare_digest(secret, self.client_secret)


class OAuth2ClientManager(
        base.CRUDManager[OAuth2Client,
        OAuth2ClientCreate,
        OAuth2ClientUpdate]):
    """OAuth2 API object manager."""


    @classmethod
    def get_by_client_id(cls, client_id: str, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> Optional[OAuth2Client]:
        """Get an API client by client ID."""
        return db.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id).one_or_none()

    @classmethod
    def get_for_user(cls, user:User, client_id: str, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> Optional[OAuth2Client]:
        """Get an API client by client ID."""
        #obj = OAuth2ClientRetrieve(user=user, client_id=client_id)
        print('GET FOR USER', user, client_id)
        return db.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id,
            OAuth2Client.user == user).one_or_none()

    @classmethod
    def fetch_for_user(cls, user:User, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> List[OAuth2Client]:
        """Get the API clients for the user."""
        return db.query(OAuth2Client).filter(OAuth2Client.user==user).all()

    @classmethod
    def delete_for_user(cls, user:User, client_id:str, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> bool:
        """Delete the specified API client."""
        obj = db.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id,
            OAuth2Client.user==user).one_or_none()
        if obj:
            db.delete(obj)
            return True
        else:
            return False

    @classmethod
    def exists(cls, user:User, name:str, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> bool:
        """Return True if a client with this name exists for the given user."""
        q = db.query(OAuth2Client).filter(
            OAuth2Client.name == name,
            OAuth2Client.user == user)
        return db.query(q.exists()).scalar()


oauth2_clients = OAuth2ClientManager(OAuth2Client)
OAuth2Client.objects = oauth2_clients
