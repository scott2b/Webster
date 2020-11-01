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
    del request.session['user_id']
    return RedirectResponse(url='/')


from .orm.oauth2.client import oauth2_clients

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
            request.session['user_id'] = _user.id
            return RedirectResponse(url='/', status_code=302)
    if request.user.is_authenticated:
        api_clients = oauth2_clients.get_by_user_id(request.user.id)
    else:
        api_clients = []
    return templates.TemplateResponse('home.html', {
        'request': request,
        'form': form,
        'api_clients': api_clients,
        'messages': messages
    })

