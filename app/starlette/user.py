from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse
from starlette.routing import Route, Router
from ..config import settings
from ..orm.oauth2client import OAuth2Client, OAuth2ClientCreate
from ..orm.user import User
from ..forms import UserForm, PasswordForm, LoginForm
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



@requires('app_auth', status_code=403)
async def profile(request):
    user = request.user
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
                add_message(request, 'Password changed', classes=['info'])
        if valid:
            return RedirectResponse(url=request.url.path, status_code=302)
    return render('user.html', {
        'user': user,
        'user_form': user_form,
        'password_form': password_form
    })
