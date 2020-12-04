"""
Schema for User
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from ..auth import get_password_hash, create_random_key


## Shared properties
#class UserBase(BaseModel):
#    email: Optional[EmailStr] = None
#    is_active: Optional[bool] = True
#    is_superuser: bool = False
#    full_name: Optional[str] = None

#AUTO_PASSWORD_BYTES = 16


class UserCreate(BaseModel):
    """Create user schema"""
    full_name: str
    email: EmailStr
    #hashed_password: str
    password: Optional[str]
    is_active: bool
    is_superuser: bool


#class UserCreateRequest(BaseModel):
#    """Create user schema. Don't inherit UserCreate or the hash_password validator
#    won't get the password!"""
#    full_name: str
#    email: EmailStr
#    password: Optional[str]
#    hashed_password: Optional[str]
#    is_active: bool
#    is_superuser: bool

#    @validator('hashed_password', always=True)
#    @classmethod
#    def hash_password(cls, v, values):
#        """Hash the password"""
#        print('values in hash validator', values)
#        if values.get('password'):
#            print('hashing password:', values['password'])
#            return get_password_hash(values['password'])
#        else:
#            print('creating a random password')
#            return get_password_hash(create_random_key(AUTO_PASSWORD_BYTES))


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


#class AdministrativeUserProfileResponse(BaseModel):
#    """Profile response to be accessible by admins only"""
#    id: int
#    full_name: str
#    email: str
#    is_active: bool
#    is_superuser: bool


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
