"""
https://docs.authlib.org/en/latest/flask/2/authorization-server.html
"""
#from __future__ import annotations # for returning self type from classmethod. remove in Py3.10
import datetime
import secrets
from typing import List, Optional
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


from typing import Optional
from pydantic import BaseModel, EmailStr


class OAuth2Base(BaseModel):

    class Config:
        arbitrary_types_allowed = True

    name: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    created_at: Optional[datetime.datetime]
    secret_expires_at: Optional[datetime.datetime]
    user: Optional[User]


class OAuth2ClientCreate(OAuth2Base):
    name: str


class OAuth2ClientUpdate(OAuth2Base):
    name: str


class OAuth2Client(base.ModelBase):
    """OAuth2 API Client model.

    TODO: user should be non-nullable
    """
    # pylint: disable=too-few-public-methods

    __tablename__ = 'oauth2_clients'
    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='name_user_id_unique_1'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, default='Primary')
    client_id = Column(String(CLIENT_ID_MAX_CHARS), unique=True, index=True, nullable=False)
    client_secret = Column(String(CLIENT_SECRET_MAX_CHARS), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    secret_expires_at = Column(Integer, nullable=True)
    user_id = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE')
    )
    user = relationship('User') # type: ignore


#class OAuth2ClientManager():

class OAuth2ClientManager(base.CRUDManager[OAuth2Client, OAuth2ClientCreate, OAuth2ClientUpdate]):
    """OAuth2 API object manager."""

    def _create(self, user:User, name:str, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> OAuth2Client:
        """Create an API client for the given user."""
        # Dep-inj not working with classmethod
        # https://github.com/ets-labs/python-dependency-injector/issues/318
        # pylint: disable=no-self-use
        db_obj = OAuth2Client(
            name=name,
            client_id=create_key(CLIENT_ID_BYTES),
            client_secret=create_key(CLIENT_SECRET_BYTES),
            user=user
        )
        db.add(db_obj)
        return db_obj

    def create(
            self, *,
            obj_in: OAuth2ClientCreate,
            db:Session = Closing[Provide[Container.closed_db]]) -> User:
        """Create a new user in the database."""
        db_obj = OAuth2Client(
            name=obj_in.name,
            client_id=create_key(CLIENT_ID_BYTES),
            client_secret=create_key(CLIENT_SECRET_BYTES),
            user=obj_in.user
        )
        db.add(db_obj)
        return db_obj

    def get_by_client_id(self, client_id: str, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> Optional[OAuth2Client]:
        """Get an API client by client ID."""
        # Dep-inj not working with classmethod
        # https://github.com/ets-labs/python-dependency-injector/issues/318
        # pylint: disable=no-self-use
        return db.query(OAuth2Client).filter(OAuth2Client.client_id == client_id).first()

    def get_by_client_id_user(self, client_id: str, user_id, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> Optional[OAuth2Client]:
        """Get an API client by client ID."""
        # Dep-inj not working with classmethod
        # https://github.com/ets-labs/python-dependency-injector/issues/318
        # pylint: disable=no-self-use
        return db.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id,
            OAuth2Client.user_id == user_id).first()

    def get_by_user_id(self, user_id:int, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> List[OAuth2Client]:
        """Get the API clients for the user."""
        # Dep-inj not working with classmethod
        # https://github.com/ets-labs/python-dependency-injector/issues/318
        # pylint: disable=no-self-use
        return db.query(OAuth2Client).filter(OAuth2Client.user_id==user_id).all()

    def delete_user_client(self, client_id:str, user:User, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> bool:
        """Delete the specified API client."""
        # Dep-inj not working with classmethod
        # https://github.com/ets-labs/python-dependency-injector/issues/318
        # pylint: disable=no-self-use
        obj = db.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id,
            User.id==user.id).first()
        if obj:
            db.delete(obj)
            return True
        else:
            return False

    def exists(self, name:str, user:User, *,
            db:Session=Closing[Provide[Container.closed_db]]
        ) -> bool:
        print('name:', name)
        print('user:', user)
        q = db.query(OAuth2Client).filter(
            OAuth2Client.name == name,
            User.id == user.id)
        #print('FRIST OBJ')
        #print(q.first())
        return db.query(q.exists()).scalar()
            


oauth2_clients = OAuth2ClientManager(OAuth2Client)
OAuth2Client.objects = oauth2_clients
