"""
Database/db-session  management resources
"""
from contextlib import contextmanager
import functools
from sqlalchemy.orm import Session
from dependency_injector.wiring import Provide
from .. import containers


@contextmanager
def session_scope(db:Session=Provide[containers.Container.db]):
    """Provides a transactional db session scope as a context block.

    There does not seem to be any performance penalty to not committing
    sessions that do not need to be committed. Thus, a no-commit option is not
    provided.
    """
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

    Note: created objects do not get a database ID until they are committed.
    Thus, if you use this to provide a session to a function, newly created
    objects will not have an ID within the function unless committed first.
    """
    @functools.wraps(f)
    async def wrapped_f(*args, **kwargs):
        with session_scope() as db:
            return await f(*args, db=db, **kwargs)
    return wrapped_f
