"""
https://docs.authlib.org/en/latest/flask/2/authorization-server.html
"""
#from __future__ import annotations # for returning self type from classmethod. remove in Py3.10
import datetime
import secrets
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship, Session
from .. import base
from ..user import User

from dependency_injector.wiring import Provide, Closing
from ...containers import Container

from . import (
    CLIENT_ID_BYTES,
    CLIENT_SECRET_BYTES,
    CLIENT_ID_MAX_CHARS,
    CLIENT_SECRET_MAX_CHARS
)


def create_key(nbytes):
    return secrets.token_urlsafe(nbytes)


class OAuth2Client(base.Base):

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


class OAuth2ClientManager():

    def create_for_user(
            cls,
            user:User,
            commit=True,
            db:Session=Provide[Container.db]
        ):
        db_obj = OAuth2Client(
            client_id=create_key(CLIENT_ID_BYTES),
            client_secret=create_key(CLIENT_SECRET_BYTES),
            user=user
        )
        db.add(db_obj)
        if commit:
            db.commit()
        return db_obj

    def get_by_client_id(cls, client_id: str,
            db:Session=Provide[Container.db]):
        return db.query(OAuth2Client).filter(OAuth2Client.client_id == client_id).first()

    def get_by_user_id(cls, user_id:int,
            db:Session=Closing[Provide[Container.db]]):
        return db.query(OAuth2Client).filter(OAuth2Client.user_id==user_id).all()
        
         
    

oauth2_clients = OAuth2ClientManager()
