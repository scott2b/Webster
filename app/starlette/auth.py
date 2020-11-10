from starlette.responses import RedirectResponse
from ..auth import verify_password_reset_token
from ..forms import PasswordForm, LoginForm
from ..messages import add_message
from .templates import render


async def login(request):
    data = await request.form()
    form = LoginForm(request, formdata=data, meta={ 'csrf_context': request.session })
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


# TODO
def password_reset(request):
    token = request.query_params['key']
    email = verify_password_reset_token(token)
    user = User.objects.get_by_email(email)
    form = PasswordForm()
