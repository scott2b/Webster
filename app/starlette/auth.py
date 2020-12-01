from starlette.responses import RedirectResponse
from starlette.routing import Route, Router
from ..auth import verify_password_reset_token
from ..forms import LoginForm, PasswordResetForm
from ..messages import add_message
from ..orm.user import User
from .templates import render


async def login(request):
    data = await request.form()
    form = LoginForm(request, formdata=data, meta={ 'csrf_context': request.session })
    if request.method == 'POST':
        user = form.validate()
        if user:
            request.session['username'] = user.email
            request.session['user_id'] = user.id
            add_message(
                request,
                f'You are now logged in as: {user.full_name}',
                classes=['info'])
            next = request.query_params.get('next', '/')
            return RedirectResponse(url=next, status_code=302)
    return render('login.html', {
        'form': form,
    })


def logout(request):
    del request.session['user_id']
    add_message(request, 'You are now logged out.', classes=['info'])
    return RedirectResponse(url='/')


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


router = Router(
    routes = [
        Route('/login', login, methods=['GET', 'POST']),
        Route('/logout', logout),
        Route('/reset-password', reset_password, methods=['GET', 'POST']),
    ]
)
