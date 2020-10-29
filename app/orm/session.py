from contextlib import contextmanager
import functools
from sqlalchemy.orm import Session
from dependency_injector.wiring import Provide
from .. import containers


@contextmanager
def session_scope(db:Session=Provide[containers.Container.db]):
    """Provides a transactional db session scope as a context block."""
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


# TODO: do we need async and non-async versions of this decorator?

def db_session(f):
    """Provided an async Sessions or SessionLocal instance to the function as
    the db parameter.

    Function must accept db, which will automatically be closed here in the
    decorator.
    """
    @functools.wraps(f)
    async def wrapped_f(*args, **kwargs):
        with session_scope() as db:
            return await f(*args, db=db, **kwargs)
    return wrapped_f
