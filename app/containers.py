from dependency_injector import containers, providers
from sqlalchemy.orm import sessionmaker
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
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))



class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    db = providers.Factory(
        SessionLocal
    )
