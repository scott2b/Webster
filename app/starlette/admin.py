from starlette.authentication import requires
from starlette.responses import RedirectResponse
from starlette.routing import Route, Router
from .templates import render
from ..auth import generate_password_reset_token
from ..config import settings
from ..forms import UserForm, AdminPasswordForm
from ..messages import add_message
from ..orm.user import User


@requires('admin_auth', status_code=403)
async def admin_users(request):
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
    return render('admin/user-list.html', {
        'form': new_user_form,
        'users': users
    })


@requires('admin_auth', status_code=403)
async def admin_user(request):
    user_id = request.path_params.get('user_id')
    user = User.objects.get(user_id)
    user_form = UserForm(request, obj=user, meta={'csrf_context': request.session})
    password_form = AdminPasswordForm(meta={'csrf_context': request.session})
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
            reset_link = f'http://localhost:8000/auth/reset-password?token={reset_token}'
            expires = settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS
            add_message(request,
                f'Reset token for {user.email} expires in {expires} hours: {reset_link}',
                classes=['info']
            )
        elif 'password-change' in data:
            password_form = AdminPasswordForm(formdata=data,
                meta={ 'csrf_context': request.session })
            valid = password_form.validate()
            if valid:
                user.set_password(password_form.new_password.data)
                add_message(request,
                    f'Password changed for user: {user.email}',
                    classes=['info'])
        if valid:
            return RedirectResponse(url=request.url.path, status_code=302)
    return render('admin/user.html', {
        'user': user,
        'user_form': user_form,
        'password_form': password_form
    })


@requires('admin_auth', status_code=403)
async def admin(request):
    return render('admin/admin.html', {})


router = Router(
    routes = [
        Route('/users/{user_id:int}', admin_user, methods=['GET', 'POST']),
        Route('/users', admin_users, methods=['GET', 'POST']),
        Route('/', admin, methods=['GET']),
    ]
)
