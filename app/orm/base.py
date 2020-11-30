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
from sqlalchemy.orm import Session
from sqlalchemy import exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from dependency_injector.wiring import Provide, Closing
import pydantic
from ..containers import Container
import sqlite3


ModelBase = declarative_base()


class DoesNotExist(Exception):
    """Object does not exist."""


class Exists(Exception):
    """Object already exists."""


class ModelExceptions():
    """Exceptions mixin for models."""

    DoesNotExist = DoesNotExist
    Exists = Exists


class DefaultSchema(pydantic.BaseModel):
    """
    Default schema for a DataModel which just allows all fields given.
    """

    class Config:
        """Configure DefaultSchema"""
        extra = 'allow'


class DataModel(ModelExceptions):
    """Subclasses should be @dataclass annotated."""
    default_schema = DefaultSchema

    def data_model(self, model=None):
        """Get the data of this instance, constructed as the specified model."""
        if model is None:
            model = self.default_schema
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

    def save(self, *,
            db:Session = Closing[Provide[Container.closed_db]]):
        """Update the data in the database."""
        if not hasattr(self, 'id') or not self.id:
            raise Exception('Unable to save model without id')
        db.add(self)
        db.commit()
        return self

ModelTypeVar = TypeVar("ModelTypeVar", bound=DeclarativeMeta, covariant=True)

class ModelTypeInterface(Protocol[ModelTypeVar]):
    """Interface for ModelType."""
    id:int

ModelType = TypeVar("ModelType", bound=ModelTypeInterface)


CreateSchemaType = TypeVar(
    "CreateSchemaType", bound=pydantic.BaseModel)
UpdateSchemaType = TypeVar(
    "UpdateSchemaType", bound=pydantic.BaseModel)


class CRUDManager(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Basic CRUD management."""

    def __init__(self, model: Type[ModelType]):
        """
        CRUD base object with default methods to Create, Read, Update, Delete.
        **Parameters**
        * `model`: An SQLAlchemy model class which also inherits from DataModel
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, id:Any,
            *, db:Session = Closing[Provide[Container.closed_db]]
    ) -> Optional[ModelType]:
        """Get an instance of ModelType by id."""
        return db.query(self.model).filter(self.model.id == id).first()

    def fetch(
            self, *, skip:int = 0, limit:int = 100,
            db:Session = Closing[Provide[Container.closed_db]]
        ) -> List[ModelType]:
        """Get instances of ModelType.

        skip: Query offset
        limit: Maximum number of items to return
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(
            self, obj_in: CreateSchemaType, *,
            db:Session = Closing[Provide[Container.closed_db]]) -> ModelType:
        """Save an instance of ModelType in the database."""
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data)  # type: ignore
        try:
            db.add(db_obj)
            db.commit()
        except exc.IntegrityError as e:
            db.rollback()
            raise self.model.Exists from e
        return db_obj

    def update(
            self, *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
            db:Session = Closing[Provide[Container.closed_db]]) -> ModelType:
        """Update the data in the database."""
        #obj_data = jsonable_encoder(db_obj)
        #obj_data = db_obj.data()
        #if isinstance(obj_in, dict):
        #    update_data = obj_in
        #elif isinstance(obj_in, self.model):
        #    update_data = obj_in.dict(exclude_unset=True)
        #else:
        #    raise Exception('Invalid model data type.')
        #for field in obj_data:
        #    if field in update_data:
        #        setattr(db_obj, field, update_data[field])
        for k, v in obj_in.dict().items():
            setattr(db_obj, k, v)
        db.add(db_obj)
        db.commit()
        return db_obj

    def delete(
            self, *, id: int,
            db:Session = Closing[Provide[Container.closed_db]]) -> ModelType:
        """Delete from the database by id."""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
