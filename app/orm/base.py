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
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import exc
from sqlalchemy.orm.decl_api import DeclarativeMeta
from dependency_injector.wiring import Provide, Closing
import pydantic
from ..containers import Container


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


class CRUDManager(Generic[ModelType]):
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

    def create(self, properties,
            db:Session=Closing[Provide[Container.closed_db]]) -> ModelType:
        obj = self.model(**properties)
        try:
            db.add(obj)
            db.commit()
        except exc.IntegrityError as e:
            db.rollback()
            raise self.model.Exists from e
        return obj

    def delete(
            self, *, id: int,
            db:Session = Closing[Provide[Container.closed_db]]) -> ModelType:
        """Delete from the database by id."""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
