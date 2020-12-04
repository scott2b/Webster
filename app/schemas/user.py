"""
Schema for User
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from ..auth import get_password_hash, create_random_key


class UserCreate(BaseModel):
    """Create user schema"""
    full_name: str
    email: EmailStr
    password: Optional[str]
    is_active: bool
    is_superuser: bool


"""
Here is an example of how FastAPI's approach to hierarchical schemas can lead
to security vulnerabilities. If we inherit a user base here which contains
is_supervisor, and then use this as the input validator to an update request
from the user, then we simply have exposed the ability for users to make
themselves superusers.

Thus, it is advisable to minimize schema inheritance, and instead be specific
about the properties of each schema. Here we create a separate administrative
validator to allow for such changes.
"""

class UserUpdateRequest(BaseModel):
    """User update request schema"""
    email: Optional[str]
    full_name: Optional[str]


class AdministrativeUserUpdateRequest(BaseModel):
    """Update to be accessible by admins only"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    password: Optional[str]
    hashed_password: Optional[str]

    @validator('hashed_password', always=True)
    @classmethod
    def hash_password(cls, v, values):
        """Hash the password"""
        if values.get('password'):
            return get_password_hash(values['password'])
        raise ValueError('Invalid password')


class UserPasswordUpdateRequest(BaseModel):
    """Password update schema"""

    password: Optional[str]
    hashed_password: Optional[str]

    @validator('hashed_password', always=True)
    @classmethod
    def hash_password(cls, v, values):
        """Hash the password"""
        if values.get('password'):
            return get_password_hash(values['password'])
        raise ValueError('Invalid password')


class UserProfileResponse(BaseModel):
    """Profile response"""
    full_name: str
    email: str
