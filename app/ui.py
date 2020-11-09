from .orm import oauth2, user
from .orm.db import db_session, session_scope
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import exc

from dependency_injector.wiring import Closing
from dependency_injector.wiring import Provide
from . import containers
from .config import settings
from .orm.oauth2.client import OAuth2Client


from starlette.requests import Request
from starlette.templating import Jinja2Templates
import inspect
import types


def _clear_messages(request):
    """Call from a template after rendering messages to clear out the current
    message list. Requires session middleware.
    """
    request.session['messages']= []
    return ''


def add_message(request, message):
    """Add a message to the session messages list."""
    if not 'messages' in request.session:
        request.session['messages'] = []
    request.session['messages'].append(message)


class Templates(Jinja2Templates):

    def TemplateResponse(
        self,
        name: str,
        context: dict,
        **kwargs
    ):
        """Render a template response.

        If it exists and is not already set in the context, injects the
        request object from the calling scope into the template context.

        Adds a clear_request method to the request instance.
        """ 
        if 'request' in context:
            req = context['request']
            if isinstance(req, Request):
                req.clear_messages = types.MethodType(_clear_messages, req)
        else:
            frame = inspect.currentframe()
            try:
                _locals = frame.f_back.f_locals
                req = _locals.get('request')
                if req is not None and isinstance(req, Request):
                    context['request'] = req
                    req.clear_messages = types.MethodType(_clear_messages, req)
            finally:
                del frame
        return super().TemplateResponse(name, context, **kwargs)
    

templates = Templates(directory='templates')


from jinja2.ext import Extension
from functools import partial
from .orm.user import User



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
        _user = User.objects.authenticate(
            email=self.email.data,
            password=self.password.data
        )
        if not _user:
            self.request.session['messages'] = ['Incorrect email or password']
        elif not _user.is_active:
            self.request.session['messages'] = ['Deactivated account']
        else:
            self.request.session['username'] = self.email.data
            self.request.session['user_id'] = _user.id
        return _user


from .orm.oauth2.client import OAuth2ClientCreate

class APIClientForm(CSRFForm):
    name = StringField('Name')

    def __init__(self, data, request, *args, **kwargs):
        self.request = request
        super().__init__(data, *args, **kwargs)

    def validate_name(self, field):
        exists = OAuth2Client.objects.exists(self.request.user, field.data) 
        if exists:
            raise validators.ValidationError(
                'Unique application name required.')


async def login(request):
    data = await request.form()
    form = LoginForm(data, request, meta={ 'csrf_context': request.session })
    if request.method == 'POST':
        user = form.validate()
        if user:
            add_message(request, f'You are now logged in as: {user.full_name}')
            add_message(request, f'You are now logged in as: {user.full_name}')
            next = request.query_params.get('next', '/')
            return RedirectResponse(url=next, status_code=302)
    return templates.TemplateResponse('login.html', {
        'form': form,
    })


def logout(request):
    del request.session['user_id']
    add_message(request, 'You are now logged out.')
    return RedirectResponse(url='/')


@requires('app_auth', status_code=403)
async def client_form(request):
    data = await request.form()
    form = APIClientForm(data, request, meta={ 'csrf_context': request.session })
    if request.method == 'POST' and 'delete' in data:
        OAuth2Client.objects.delete_for_user(request.user, data['client_id'])
        next = request.query_params.get('next', '/')
        return RedirectResponse(url=next, status_code=302)
    if request.method == 'POST' and form.validate():
        _client = OAuth2Client.objects.create(
            OAuth2ClientCreate(user=request.user, **data))
        next = request.query_params.get('next', '/')
        return RedirectResponse(url=next, status_code=302)
    return templates.TemplateResponse('_client.html', {
        'form': form,
    })

from starlette.responses import JSONResponse


async def homepage(request):

    data = await request.form()
    form = LoginForm(data, request, meta={ 'csrf_context': request.session })
    client_form = APIClientForm(data, request, meta={ 'csrf_context': request.session })
    if request.user.is_authenticated:
        api_clients = OAuth2Client.objects.fetch_for_user(request.user)
    else:
        api_clients = []
    return templates.TemplateResponse('home.html', {
        'form': form,
        'client_form': client_form,
        'api_clients': api_clients,
    })
