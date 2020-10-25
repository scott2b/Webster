from dependency_injector import containers, providers
from .orm.session import SessionLocal

class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    database_client = providers.Factory(
        SessionLocal
    )
