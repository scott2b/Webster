from starlette.authentication import requires
from starlette.responses import RedirectResponse
from starlette.routing import Route, Router
from .templates import render
from ..auth import generate_password_reset_token
from ..config import settings
from ..forms import UserForm, AdminPasswordForm, UserDeleteForm
from ..messages import add_message
from ..orm.user import User
from ..schemas.user import UserCreate


@requires('admin_auth', status_code=403)
async def admin_users(request):
    data = await request.form()
    new_user_form = UserForm(request,
        formdata=data or None, meta={ 'csrf_context': request.session })
    if not data:
        # A default value on the form object field would propagate if the UI
        # form value is unselected. Thus, we set the default dynamically here.
        new_user_form.is_active.data = True
    if request.method == 'POST' and new_user_form.validate():
        try:
            properties = UserCreate(**new_user_form.data).dict()
            user = User.objects.create(properties)
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
    user_delete_form = UserDeleteForm(meta={'csrf_context': request.session})
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
                add_message(request, f'User updated', key='user_info')
        elif 'password-reset' in data:
            reset_token = generate_password_reset_token(user.email)
            reset_link = f'{settings.SERVER_HOST}/auth/reset-password?token={reset_token}'
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
        elif 'delete-user' in data:
            user_delete_form = UserDeleteForm(formdata=data,
                meta={ 'csrf_context': request.session })
            valid = user_delete_form.validate()
            verify_email = user_delete_form.email.data
            if verify_email == user.email:
                User.objects.delete(id=user.id)
                add_message(request,
                    f'Deleted user: {verify_email}',
                    classes=['info'])
                return RedirectResponse(url='/admin/users', status_code=302)
            else:
                user_delete_form.email.errors = \
                    ['Incorrect email. User not deleted.']
        if valid:
            return RedirectResponse(url=request.url.path, status_code=302)
    return render('admin/user.html', {
        'user': user,
        'user_form': user_form,
        'password_form': password_form,
        'user_delete_form': user_delete_form
    })


@requires('admin_auth', status_code=403)
async def admin(request):
    return render('admin/admin.html', {})


router = Router(
    routes = [
        Route('/users/{user_id:int}', admin_user, name='user', methods=['GET', 'POST']),
        Route('/users', admin_users, name='users', methods=['GET', 'POST']),
        Route('/', admin, name='home', methods=['GET']),
    ]
)
