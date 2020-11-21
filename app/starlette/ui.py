from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse
from starlette.routing import Route, Router
from ..orm.oauth2client import OAuth2Client, OAuth2ClientCreate
from ..orm.user import User
from ..forms import UserForm, PasswordForm, LoginForm, APIClientForm
from ..messages import add_message
from .templates import render


async def homepage(request):
    data = await request.form()
    login_form = LoginForm(request, meta={ 'csrf_context': request.session })
    return render('home.html', {
        'login_form': login_form,
    })


@requires('admin_auth', status_code=403)
async def users(request):
    users = User.objects.fetch()
    return render('user-list.html', {
        'users': users
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


router = Router(
    routes = [
        Route('/me', update_user, methods=['GET', 'POST']),
        Route('/{user_id:int}', update_user, methods=['GET', 'POST']),
        Route('/', users, methods=['GET']),
    ]
)
