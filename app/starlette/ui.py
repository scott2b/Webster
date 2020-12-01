from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse
from starlette.routing import Route, Router
from ..config import settings
from ..orm.oauth2client import OAuth2Client, OAuth2ClientCreate
from ..orm.user import User
from ..forms import UserForm, PasswordForm, LoginForm, APIClientForm, PasswordResetForm
from ..messages import add_message
from ..schemas.user import UserCreateRequest
from .templates import render
from ..auth import generate_password_reset_token, verify_password_reset_token

async def homepage(request):
    data = await request.form()
    login_form = LoginForm(request, meta={ 'csrf_context': request.session })
    return render('home.html', {
        'project_name': settings.PROJECT_NAME,
        'login_form': login_form,
    })


@requires('admin_auth', status_code=403)
async def users(request):
    data = await request.form()
    new_user_form = UserForm(request,
        formdata=data, meta={ 'csrf_context': request.session })
    if request.method == 'POST' and new_user_form.validate():
        try:
            user = User.objects.create(UserCreateRequest(**new_user_form.data))
            return RedirectResponse(url=f'/admin/users/{user.id}', status_code=302)
        except User.Exists:
            new_user_form.email.errors = \
                ['A user with that email address already exists']
    users = User.objects.fetch()
    return render('user-list.html', {
        'form': new_user_form,
        'users': users
    })


async def reset_password(request):
    data = await request.form()
    form = PasswordResetForm(formdata=data, meta={ 'csrf_context': request.session })
    if request.method == 'GET':
        token = request.query_params['token'] 
        form.token.data = token
    email = verify_password_reset_token(form.token.data)
    if request.method == 'POST' and form.validate():
        user = User.objects.get_by_email(email)
        user.set_password(form.new_password.data)
        add_message(request,
            'You may now sign in with your new password.',
            classes=['info']
        )
        return RedirectResponse(url='/auth/login', status_code=302)
    return render('password-reset.html', {
        'email': email,
        'form': form 
    })


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
        elif 'password-reset' in data:
            reset_token = generate_password_reset_token(user.email)
            reset_link = f'http://localhost:8000/users/reset-password?token={reset_token}'
            expires = settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS
            add_message(request,
                f'Reset token for {user.email} expires in {expires} hours: {reset_link}',
                classes=['info']
            )
        elif 'password-change' in data:
            password_form = PasswordForm(user, formdata=data,
                meta={ 'csrf_context': request.session })
            valid = password_form.validate() and user.change_password(
                password_form.current_password.data,
                password_form.new_password.data)
            if valid:
                add_message(request, 'Password changed', classes=['info'])
        if valid:
            return RedirectResponse(url=request.url.path, status_code=302)
    return render('user.html', {
        'user': user,
        'user_form': user_form,
        'password_form': password_form
    })


router = Router(
    routes = [
        Route('/me', update_user, methods=['GET', 'POST']),
        Route('/{user_id:int}', update_user, methods=['GET', 'POST']),
        Route('/', users, methods=['GET', 'POST']),
    ]
)
