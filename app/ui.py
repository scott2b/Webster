from .orm import oauth2, user
from .orm.db import db_session, session_scope
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.templating import Jinja2Templates
from starlette.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import exc

from dependency_injector.wiring import Closing
from dependency_injector.wiring import Provide
from . import containers
from .config import settings
from .orm.oauth2.client import OAuth2Client

templates = Jinja2Templates(directory='templates')

from jinja2.ext import Extension
from functools import partial
from .orm.user import User


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
        if _user:
            return True
        else:
            return False

from .orm.oauth2.client import OAuth2ClientCreate, OAuth2Base

class APIClientForm(CSRFForm):
    name = StringField('Name')

    def __init__(self, data, request, *args, **kwargs):
        self.request = request
        super().__init__(data, *args, **kwargs)

    def validate_name(self, field):
        exists = OAuth2Client.objects.exists(field.data, self.request.user) 
        if exists:
            raise validators.ValidationError(
                'Unique application name required.')


#def create_client(name, user):
#    obj = OAuth2ClientCreate(
#        name=name,
#        user=user
#    )
#    _client = None
#    with session_scope() as db:
#        try:
#            _client = OAuth2Client.objects.create(obj_in=obj, db=db)
#        except exc.IntegrityError:
#            db.rollback()
#            self.request.session['messages'] = ['Please provide a unique client name.']
#            v = False


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


@requires('app_auth', status_code=403)
async def client_form(request):
    data = await request.form()
    form = APIClientForm(data, request, meta={ 'csrf_context': request.session })
    if request.method == 'POST' and 'delete' in data:
        OAuth2Client.objects.delete_user_client(data['client_id'], request.user)
        next = request.query_params.get('next', '/')
        return RedirectResponse(url=next, status_code=302)
    if request.method == 'POST' and form.validate():
        obj = OAuth2ClientCreate(
            name=form.name.data,
            user=request.user
        )
        _client = OAuth2Client.objects.create(obj_in=obj)
        next = request.query_params.get('next', '/')
        return RedirectResponse(url=next, status_code=302)
    clear_messages = partial(_clear_messages, request)
    return templates.TemplateResponse('_client.html', {
        'request': request,
        'form': form,
        'clear_messages': clear_messages
    })

from starlette.responses import JSONResponse


async def homepage(request):

    data = await request.form()
    form = LoginForm(data, request, meta={ 'csrf_context': request.session })
    client_form = APIClientForm(data, request, meta={ 'csrf_context': request.session })
    if request.user.is_authenticated:
        print('user id', request.user.id)
        api_clients = OAuth2Client.objects.get_by_user_id(request.user.id)
    else:
        api_clients = []
    clear_messages = partial(_clear_messages, request)
    return templates.TemplateResponse('home.html', {
        'request': request,
        'form': form,
        'client_form': client_form,
        'api_clients': api_clients,
        'clear_messages': clear_messages,
    })
