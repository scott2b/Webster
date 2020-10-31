from .orm import oauth2, user
from .orm.db import db_session, session_scope
from starlette.exceptions import HTTPException
from starlette.templating import Jinja2Templates
from starlette.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from dependency_injector.wiring import Closing
from dependency_injector.wiring import Provide
from . import containers

templates = Jinja2Templates(directory='templates')


from wtforms import Form, BooleanField, StringField, validators, PasswordField


class LoginForm(Form):
    email = StringField('Email Address', [validators.Email()])
    password = PasswordField('Password')


def logout(request):
    del request.session['username']
    return RedirectResponse(url='/')


async def homepage(request):
    messages = []
    form = LoginForm(await request.form())
    if request.method == 'POST' and form.validate():
        _user = user.users.authenticate(
            email=form.email.data,
            password=form.password.data
        )
        if not _user:
            messages.append('Incorrect email or password')
        elif not user.users.is_active(_user):
            messages.append('Deactivated account')
        else:
            request.session['username'] = form.email.data
            return RedirectResponse(url='/', status_code=302)
    return templates.TemplateResponse('home.html', {
        'request': request,
        'form': form,
        'messages': messages
    })

