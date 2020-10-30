from dependency_injector import containers, providers
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy import create_engine
from .config import settings


### SQLAlchemy sessions ###

# async not generally available yet. Watch for SQLAlchemy v1.4 or v2.0
#from sqlalchemy.ext.asyncio import create_async_engine
#from sqlalchemy.ext.asyncio import AsyncSession


engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
# Can we have 2 different session factories on the same engine?!!
# Just going with SessionLocal for now to see how it goes.
#Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))


def get_closed_db() -> Session:
    """Yield a db session that is closed when the function is exited. Note, to
    work properly, this needs to be provided as a Resource (not a Factory),
    and must be injected with the Closing operator. E.g:

    ```
    from dependency_injector.wiring import Closing, Provide
    def myfunc(db:Session=Closing[Provide[Container.closed_db]])...
    ```

    If not provided via Closing, you will potentially leaking sessions ...
    although this may not be a real issue if using a thread-local scoped
    session.

    Example code tends not to use this in the application layer, but it is
    handy in the ORM layer for providing alternative Session lifecycles. This
    requires expire_on_commit=False as above.
    """
    db = SessionLocal()
    try:
        print('YIELDING CLOSED DB')
        yield db
        print('YIELDED. COMMITTING')
        db.commit()
        print('COMMITTED CLOSED DB')
    except:
        print('ROLLBACK CLOSED DB')
        db.rollback()
        print('ROLLED BACK')
        raise
    finally:
        print('CLOSING CLOSED DB')
        db.close()
        print('CLOSED')


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    db = providers.Factory(
        SessionLocal
    )

    closed_db = providers.Resource(
        get_closed_db
    )
