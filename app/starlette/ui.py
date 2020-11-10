from ..orm import user
from ..orm.db import db_session, session_scope
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import exc

from dependency_injector.wiring import Closing
from dependency_injector.wiring import Provide
from .. import containers
from ..orm.oauth2client import OAuth2Client, OAuth2ClientCreate

from ..forms import UserForm, PasswordForm, LoginForm, APIClientForm
from ..messages import add_message


from .templates import Templates
render = Templates(directory='templates').TemplateResponse


from jinja2.ext import Extension
from functools import partial
from ..orm.user import User


async def login(request):
    data = await request.form()
    form = LoginForm(data, request, meta={ 'csrf_context': request.session })
    if request.method == 'POST':
        user = form.validate()
        if user:
            request.session['username'] = user.email
            request.session['user_id'] = user.id
            add_message(request, f'You are now logged in as: {user.full_name}')
            next = request.query_params.get('next', '/')
            return RedirectResponse(url=next, status_code=302)
    return render('login.html', {
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
    return render('_client.html', {
        'form': form,
    })


async def homepage(request):
    data = await request.form()
    form = LoginForm(data, request, meta={ 'csrf_context': request.session })
    client_form = APIClientForm(data, request, meta={ 'csrf_context': request.session })
    if request.user.is_authenticated:
        api_clients = OAuth2Client.objects.fetch_for_user(request.user)
    else:
        api_clients = []
    return render('home.html', {
        'form': form,
        'client_form': client_form,
        'api_clients': api_clients,
    })


@requires('admin_auth', status_code=403)
async def users(request):
    users = User.objects.fetch()
    return render('user-list.html', {
        'users': users
    })


from ..schemas.user import UserCreateRequest
from ..auth import generate_password_reset_token, verify_password_reset_token


@requires('app_auth', status_code=403)
async def update_user(request):
    if request.url.path.endswith('/me'):
        user = request.user
    else:
        user_id = request.path_params.get('user_id')
        if user_id != request.user.id and not 'admin_auth' in request.auth.scopes:
            raise HTTPException(403, detail='Not authorized')
        user = User.objects.get(user_id)
    user_form = UserForm(request, obj=user, meta={'csrf_context': request.session})
    password_form = PasswordForm(user, meta={'csrf_context': request.session})
    data = await request.form()
    if request.method == 'POST':
        valid = False
        if 'user-info' in data:
            user_form = UserForm(request, formdata=data, obj=user,
                meta={ 'csrf_context': request.session })
            valid = user_form.validate()
            if valid:
                user_form.populate_obj(user) 
                user.save()
        elif 'password-change' in data:
            password_form = PasswordForm(user, formdata=data,
                meta={ 'csrf_context': request.session })
            valid = password_form.validate() and user.change_password(
                password_form.current_password.data,
                password_form.new_password.data)
            if valid:
                add_message(request, 'Password changed')
        if valid:
            return RedirectResponse(url=request.url.path, status_code=302)
    return render('user.html', {
        'user': user,
        'user_form': user_form,
        'password_form': password_form
    })


def password_reset(request):
    token = request.query_params['key']
    email = verify_password_reset_token(token)
    user = User.objects.get_by_email(email)
    form = PasswordForm()
