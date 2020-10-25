from dependency_injector import containers, providers
#from .orm.session import SessionLocal


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

#from sqlalchemy.ext.asyncio import create_async_engine
#from sqlalchemy.ext.asyncio import AsyncSession

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


#engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



#class DatabaseContainer(containers.DeclarativeContainer):
#
#    #config = providers.Configuration()
#
#    database_client = providers.Factory(
#        SessionLocal
#    )


class Container(containers.DeclarativeContainer):

    #config = providers.Configuration()

    #database_client = providers.Factory(
    #    SessionLocal
    #)

    #db = providers.Container(
    #    DatabaseContainer
    #)

    db = providers.Factory(
        SessionLocal
    )
