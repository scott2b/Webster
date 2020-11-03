from typing import Generator
from dependency_injector import containers, providers
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy import create_engine
from .config import settings


### SQLAlchemy sessions ###

# async not generally available yet. Watch for SQLAlchemy v1.4 or v2.0
#from sqlalchemy.ext.asyncio import create_async_engine
#from sqlalchemy.ext.asyncio import AsyncSession


"""
Use scope_session for thread-local scoping to avoid session leaks.
"""
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
#SessionLocal = scoped_session(sessionmaker(
#    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))


"""
SQLAlchemy connection count provided for testing and debugging purposes.
"""
from sqlalchemy import event
connection_count = 0


@event.listens_for(engine, 'checkin')
def receive_checkin(dbapi_connection, connection_record):
    global connection_count
    connection_count -= 1


@event.listens_for(engine, 'checkout')
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    global connection_count
    connection_count += 1


def get_closed_db() -> Generator:
    """Yield a db session that is closed when the function is exited. Note, to
    work properly, this needs to be provided as a Resource (not a Factory),
    and must be injected with the Closing operator. E.g:

    WARNING: The yielded session object cannot be error-handled in this scope.
    Thus, rollback and connection close will not occur as a result of
    exceptions in target functions.

    This service **should only be used with thread-local scope** (as built by
    scoped_session above) and with the Closing dependency injection directive. 

    ```
    from dependency_injector.wiring import Closing, Provide
    def myfunc(db:Session=Closing[Provide[Container.closed_db]])...
    ```

    Example code tends not to use this in the application layer, but it is
    handy in the ORM layer for providing alternative Session lifecycles. This
    requires expire_on_commit=False as set above so that objects returned from
    the orm layer are still usable after the session is closed.

    There does not seem to be any performance penalty for committing sessions
    that do not really need to be committed. Thus, a no-commit option is not
    provided.
    """
    db = SessionLocal()
    yield db
    db.commit()
    db.close()


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    # Do not use this with the Closing directive
    db = providers.Factory(
        SessionLocal
    )

    # For use with Closing.
    # Use only with scoped_session thread-local scope.
    closed_db = providers.Resource(
        get_closed_db
    )
