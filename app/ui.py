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
from .orm.oauth2.client import oauth2_clients

templates = Jinja2Templates(directory='templates')

from jinja2.ext import Extension
from functools import partial



def _clear_messages(request):
    request.session['messages']= []
    return ''


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

    def __init__(self, data, request, *args, **kwargs):
        self.request = request
        super().__init__(data, *args, **kwargs)

    def validate(self):
        v = super().validate()
        if not v:
            return False
        _user = user.users.authenticate(
            email=self.email.data,
            password=self.password.data
        )
        if not _user:
            self.request.session['messages'] = ['Incorrect email or password']
        elif not user.users.is_active(_user):
            self.request.session['messages'] = ['Deactivated account']
        else:
            self.request.session['username'] = self.email.data
            self.request.session['user_id'] = _user.id
        if _user:
            return True
        else:
            return False


async def login(request):
    data = await request.form()
    form = LoginForm(data, request, meta={ 'csrf_context': request.session })
    if request.method == 'POST' and form.validate():
        next = request.query_params.get('next', '/')
        return RedirectResponse(url=next, status_code=302)
    clear_messages = partial(_clear_messages, request)
    return templates.TemplateResponse('login.html', {
        'request': request,
        'form': form,
        'clear_messages': clear_messages
    })


def logout(request):
    del request.session['user_id']
    return RedirectResponse(url='/')


async def homepage(request):

    data = await request.form()
    form = LoginForm(data, request, meta={ 'csrf_context': request.session })
    if request.method == 'POST' and form.validate():
        return RedirectResponse(url='/', status_code=302)

    if request.user.is_authenticated:
        api_clients = oauth2_clients.get_by_user_id(request.user.id)
    else:
        api_clients = []
    clear_messages = partial(_clear_messages, request)
    return templates.TemplateResponse('home.html', {
        'request': request,
        'form': form,
        'api_clients': api_clients,
        'clear_messages': clear_messages
    })
