from typing import Optional
from pydantic import BaseModel, EmailStr, ValidationError


## Shared properties
#class UserBase(BaseModel):
#    email: Optional[EmailStr] = None
#    is_active: Optional[bool] = True
#    is_superuser: bool = False
#    full_name: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(BaseModel):
    email: EmailStr
    password: str

from ..auth import get_password_hash, verify_password
from pydantic import validator


"""
Here is a good example of how FastAPI's approach to hierarchical schemas can
lead to security vulnerabilities. If we inherit a user base here which contains
is_supervisor, and then use this as the input validator to an update request
from the user, then we simply have exposed the ability for users to make
themselves superusers.

Thus, it is advisable to minimize schema inheritance, and instead be specific
about the properties of each schema. Here we create a separeate administrative
validator to allow for such changes.
"""

class UserUpdateRequest(BaseModel):
    email: Optional[str]
    full_name: Optional[str]


class AdministrativeUserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None


class UserPasswordUpdateRequest(BaseModel):

    password: Optional[str]
    hashed_password: Optional[str]

    @validator('hashed_password', always=True)
    @classmethod
    def hash_password(cls, v, values):
        if values.get('password'):
            return get_password_hash(values['password'])
        raise ValueError('Invalid password')


#class UserInDBBase(UserBase):
#    id: Optional[int] = None
#
#    class Config:
#        orm_mode = True


# Additional properties to return via API
#class User(UserInDBBase):
#    pass


# Additional properties stored in DB
#class UserInDB(UserInDBBase):
#    hashed_password: str
