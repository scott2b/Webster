from .orm import oauth2, user
from .orm.db import db_session, session_scope
from starlette.exceptions import HTTPException
from starlette.templating import Jinja2Templates
from starlette.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from dependency_injector.wiring import Closing
from dependency_injector.wiring import Provide
from . import containers
from .config import settings

templates = Jinja2Templates(directory='templates')


from wtforms import Form, BooleanField, StringField, validators, PasswordField

from wtforms.csrf.session import SessionCSRF
from datetime import timedelta


class CSRFForm(Form):

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = settings.CSRF_KEY.encode()
        csrf_time_limit = timedelta(minutes=20)


class LoginForm(CSRFForm):
    email = StringField('Email Address', [validators.Email()])
    password = PasswordField('Password')


def logout(request):
    del request.session['username']
    return RedirectResponse(url='/')


async def homepage(request):
    messages = []
    data = await request.form()
    form = LoginForm(data, meta={ 'csrf_context': request.session })
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

