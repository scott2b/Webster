"""User ORM model and object manager."""
import copy
from dataclasses import dataclass
from typing import Optional
from dependency_injector.wiring import Closing, Provide
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import Session
from sqlalchemy import exc
from . import base
from ..auth import get_password_hash, verify_password, create_random_key
from ..schemas.user import UserCreate, UserUpdateRequest, UserProfileResponse
from ..containers import Container

AUTO_PASSWORD_BYTES = 16

@dataclass
class User(base.ModelBase, base.DataModel):
    """User model."""

    __tablename__ = "users"
    default_schema = UserProfileResponse

    id:int = Column(Integer, primary_key=True, index=True)
    full_name:str = Column(String, index=True)
    email:str = Column(String, unique=True, index=True, nullable=False)
    hashed_password:str = Column(String, nullable=False)
    is_active:bool = Column(Boolean(), default=True)
    is_superuser:bool = Column(Boolean(), default=False)

    @property
    def is_authenticated(self):
        """All user objects are authenticated."""
        return True

    def verify_user_password(self, password):
        print('input pw:', password)
        print('hashed input', get_password_hash(password))
        print('user hashed pw', self.hashed_password)
        return verify_password(password, self.hashed_password)

    def change_password(self, current_password, new_password):
        if verify_password(current_password, self.hashed_password):
            self.hashed_password = get_password_hash(new_password)
            self.save()
            return True
        else:
            return False

    def set_password(self, password, db):
        self.hashed_password = get_password_hash(password)
        self.save(db=db)


class UserManager(base.CRUDManager[User]):
    """User object manager."""

    @classmethod
    def get_by_email(cls, email: str, *,
            db:Session = Closing[Provide[Container.closed_db]]) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()

    @classmethod
    def authenticate(cls, email: str, password: str, *,
            db:Session = Closing[Provide[Container.closed_db]]) -> Optional[User]:
        """Return a user by email address if the provided password verifies."""
        user = cls.get_by_email(email, db=db)
        if not user:
            return None
        if not user.verify_user_password(password):
            return None
        return user

    def create(self, properties, db:Session=Closing[Provide[Container.closed_db]]) -> Optional[User]:
        properties = copy.copy(properties)
        if properties.get('password'):
            properties['hashed_password']= get_password_hash(properties['password'])
        else:
            pw = create_random_key(AUTO_PASSWORD_BYTES)
            properties['hashed_password'] = get_password_hash(pw)
        if 'password' in properties:
            del properties['password']
        return super().create(properties, db=db)

users = UserManager(User)
User.objects = users
