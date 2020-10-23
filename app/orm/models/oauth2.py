"""
https://docs.authlib.org/en/latest/flask/2/authorization-server.html
"""
from authlib.integrations.sqla_oauth2 import OAuth2ClientMixin
from authlib.integrations.sqla_oauth2 import OAuth2TokenMixin
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ..base import Base


class OAuth2Client(Base, OAuth2ClientMixin):

    __tablename__ = 'oauth2_clients'

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE')
    )
    user = relationship('User')


class OAuth2Token(Base, OAuth2TokenMixin):

    __tablename__ = 'oauth2_tokens'

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE')
    )
    user = relationship('User')
