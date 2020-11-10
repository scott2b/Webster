"""
Message schema
"""
from pydantic import BaseModel


class Msg(BaseModel):
    """Message schema"""
    msg: str
