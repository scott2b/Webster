"""
Base utilities for ORM

This is mostly lifted from FastAPI, although there seem to be some issues with
how typing is handled. It helps to have sqlalchemy-stubs installed, but does
not solve the problem of no `id` property existing on Base.

Details about use of typing in FastAPI are here:
https://fastapi.tiangolo.com/python-types/
"""
import dataclasses
from typing import Any, Dict, Generic, List, Optional, Protocol
from typing import Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from dependency_injector.wiring import Provide, Closing
import pydantic
from ..containers import Container



#def make_declarative_base(self):
#    """Creates the declarative base."""
#    # https://stackoverflow.com/a/22700629
#    base = declarative_base(cls=Model, name='Model',
#                            metaclass=_BoundDeclarativeMeta)
#    base.query = _QueryProperty(self)
#    return base

ModelBase = declarative_base()


class DoesNotExist(Exception):
    """Object does not exist."""


class Exists(Exception):
    """Object already exists."""


class ModelExceptions():

    DoesNotExist = DoesNotExist
    Exists = Exists


class BaseBase(pydantic.BaseModel):
    """
    Default Base schema for a DataModel which just allows all fields given.
    """

    class Config:
        extra = 'allow'


class DataModel():
    """Subclasses should be @dataclass annotated."""
    base_schema = BaseBase
    
    def data_model(self, model=None):
        if model is None:
            model = self.base_schema
        data = dataclasses.asdict(self)
        data = model(**data)
        return data

    def dict(self, model=None):
        """Return the validated data as a dictionary."""
        _d = self.data_model(model=model)
        return _d.dict()

    def json(self, model=None):
        """Return the validated data as a JSON string."""
        _d = self.data_model(model=model)
        return _d.json()


ModelTypeVar = TypeVar("ModelTypeVar", bound=DeclarativeMeta, covariant=True)

class ModelTypeInterface(Protocol[ModelTypeVar]):
    """Interface for ModelType."""
    # pylint: disable=too-few-public-methods
    id:int

ModelType = TypeVar("ModelType", bound=ModelTypeInterface)


CreateSchemaType = TypeVar(
    "CreateSchemaType", bound=pydantic.BaseModel)  # pylint: disable=no-member
UpdateSchemaType = TypeVar(
    "UpdateSchemaType", bound=pydantic.BaseModel)  # pylint: disable=no-member


class CRUDManager(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Basic CRUD management."""

    def __init__(self, model: Type[ModelType]):
        """
        CRUD base object with default methods to Create, Read, Update, Delete.
        **Parameters**
        * `model`: An SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, id:Any,  # pylint: disable=redefined-builtin
            *, db:Session = Closing[Provide[Container.closed_db]]
    ) -> Optional[ModelType]:
        """Get an instance of ModelType by id."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
            self, *, skip:int = 0, limit:int = 100,
            db:Session = Closing[Provide[Container.closed_db]]) -> List[ModelType]:
        """Get instances of ModelType.

        skip: Query offset
        limit: Maximum number of items to return
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(
            self, *, obj_in: CreateSchemaType,
            db:Session = Closing[Provide[Container.closed_db]]) -> ModelType:
        """Save an instance of ModelType in the database."""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        return db_obj

    def update(
            self, *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
            db:Session = Closing[Provide[Container.closed_db]]) -> ModelType:
        """Update the data in the database."""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        elif isinstance(obj_in, self.model):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            raise Exception('Invalid model data type.')
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        return db_obj

    def delete(
            self, *, id: int,  # pylint:disable=redefined-builtin
            db:Session = Closing[Provide[Container.closed_db]]) -> ModelType:
        """Delete from the database by id."""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        return obj
