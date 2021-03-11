import click
from . import orm, schemas
from .orm.db import session_scope
from .orm.user import User
#from fastapi.encoders import jsonable_encoder

from .containers import SessionLocal


# users group

@click.group()
def users():
    pass

@click.command()
@click.argument('full_name')
@click.argument('email')
@click.argument('password')
@click.option('--superuser', is_flag=True, default=False)
def create_user(full_name, email, password, superuser):
    properties = {
       'full_name': full_name,
       'email': email,
       'password': password,
       'is_superuser': superuser
    }
    session = SessionLocal()
    try:
        from .orm.user import users
        users.create(properties, db=session)
    except:
        session.rollback()
        raise
    session.commit()


@click.command()
@click.argument('email')
@click.argument('password')
def update_user(email, password):
    session = SessionLocal()
    user = User.objects.get_by_email(email=email, db=session)
    #user_data = jsonable_encoder(user)
    #user_in = schemas.user.AdministrativeUserUpdateRequest(**user_data)
    obj_in = schemas.user.AdministrativeUserUpdateRequest(password=password,
        **user.dict())
    user = User.objects.update(db_obj=user, obj_in=obj_in, db=session)


@click.command()
@click.argument('email')
@click.option('--create', is_flag=True)
def create_client(email, create):
    session = SessionLocal()
    from .orm.user import users
    user = users.get_by_email(email=email, db=session)
    if create:
        from .orm.oauth2.client import oauth2_clients
        client = oauth2_clients.create_for_user(user, db=session)
        print(client) # todo, make this readable
    else:
        pass # todo, output a user's clients


users.add_command(create_user, 'create')
users.add_command(update_user, 'update')
users.add_command(create_client, 'client')

# main cli group

@click.group()
def cli():
    pass

cli.add_command(users)


if __name__ == '__main__':
    cli()



