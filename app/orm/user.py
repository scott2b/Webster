"""User ORM model and object manager."""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from dependency_injector.wiring import Closing, Provide
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import Session
from . import base
from ..auth import get_password_hash, verify_password
from ..schemas.user import UserCreate, UserUpdate
from ..containers import Container

import pydantic

from pydantic import BaseModel, EmailStr

### Schema

class UserBase(BaseModel):
    id: int
    full_name: str
    email: str
    hashed_password: str
    is_active: bool
    is_superuser: bool


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    is_superuser: bool


### ORM

@dataclass
class User(base.ModelBase, base.DataModel):
    """User model."""
    # pylint: disable=too-few-public-methods

    __tablename__ = "users"
    base_schema = UserBase

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


class UserManager(base.CRUDManager[User, UserCreate, UserUpdate]):
    """User object manager."""

    @classmethod
    def get_by_email(cls, email: str, *,
            db:Session = Closing[Provide[Container.closed_db]]) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()

    @classmethod
    def create(cls, *,
            obj_in: UserCreate,
            db:Session = Closing[Provide[Container.closed_db]]) -> User:
        """Create a new user in the database."""
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        return db_obj

    @classmethod
    def update(cls, *,
            db_obj: User,
            obj_in: Union[UserUpdate, Dict[str, Any]],
            db:Session = Closing[Provide[Container.closed_db]]) -> User:
        """Update user object data in the database."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db_obj=db_obj, obj_in=update_data, db=db)

    @classmethod
    def authenticate(cls, email: str, password: str, *,
            db:Session = Closing[Provide[Container.closed_db]]) -> Optional[User]:
        """Return a user by email address if the provided password verifies."""
        user = cls.get_by_email(email, db=db)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


users = UserManager(User)
User.objects = users
