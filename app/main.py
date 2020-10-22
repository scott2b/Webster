import databases
from starlette.applications import Starlette
from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser
from starlette.exceptions import HTTPException
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles
from .config import settings


from . import orm


#database = databases.Database(settings.SQLALCHEMY_DATABASE_URI)

from typing import Generator

def get_db() -> Generator:
    try:
        db = orm.SessionLocal()
        yield db
    finally:
        db.close()



#def auth(request):
#    user = orm.users.authenticate(
#        database, email=form_data.username, password=form_data.password
#    )
#    if not user:
#        raise HTTPException(status_code=400, detail="Incorrect email or password")
#    elif not orm.users.is_active(user):
#        raise HTTPException(status_code=400, detail="Inactive user")
#    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#    return {
#        "access_token": auth.create_access_token(
#            user.id, expires_delta=access_token_expires
#        ),
#        "token_type": "bearer",
#    }


class SessionAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        if 'username' in request.session:
            username = request.session['username']
            return AuthCredentials(["authenticated"]), SimpleUser(username)
        elif request.headers.get('key'):
            key = request.headers['key']
            print('KEY', key)
            if key == '123':
                return AuthCredentials(["authenticated"]), SimpleUser(key)


def logout(request):
    del request.session['username']
    return RedirectResponse(url='/')


async def homepage(request):
    if request.method == 'POST':
        form = await request.form()
        db = orm.SessionLocal()
        user = orm.users.authenticate(
            db, email=form['username'], password=form['password']
        )
        db.close()
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        elif not orm.users.is_active(user):
            raise HTTPException(status_code=400, detail="Inactive user")
        request.session['username'] = form['username']
    return HTMLResponse(f"""
<html>
<body>
    hello {request.session.get('username')}
    <form action="." method="POST">
        <input name="username" type="text" />
        <input name="password" type="text" />
        <input type="submit" />
    </form>
</body>
</html>
""")


def user_me(request):
    username = "John Doe"
    return PlainTextResponse('Hello, %s!' % username)

def user(request):
    username = request.path_params['username']
    return PlainTextResponse('Hello, %s!' % username)

async def websocket_endpoint(websocket):
    await websocket.accept()
    await websocket.send_text('Hello, websocket!')
    await websocket.close()

def startup():
    print('Ready to go')


routes = [
    Route('/', homepage, methods=['GET', 'POST']),
    Route('/logout', logout),
    Route('/user/me', user_me),
    Route('/user/{username}', user),
    WebSocketRoute('/ws', websocket_endpoint),
    Mount('/static', StaticFiles(directory="static")),
]

app = Starlette(
    debug=True,
    routes=routes,
    on_startup=[startup])


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.add_middleware(
    AuthenticationMiddleware,
    backend=SessionAuthBackend())

app.add_middleware(
    SessionMiddleware,
    secret_key='supersecret',
    #session_cookie='basicapi_session',
    # max_age # seconds, defaults to 2 weeks
    # same_site # defaults to 'lax'
    https_only=False)

