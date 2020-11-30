from starlette.authentication import requires
from starlette.responses import RedirectResponse
from ..forms import UserForm, PasswordForm, LoginForm, APIClientForm
from ..messages import add_message
from ..orm.oauth2client import OAuth2Client, OAuth2ClientCreate
from .templates import render


@requires('app_auth', status_code=403)
async def client_apps(request):
    data = await request.form()
    form = APIClientForm(request, formdata=data, meta={ 'csrf_context': request.session })
    if request.method == 'POST' and 'delete' in data:
        OAuth2Client.objects.delete_for_user(request.user,
            client_id=data['client_id'])
        add_message(
            request,
            f'Deleted app with client ID: {data["client_id"]}',
            classes=['info']
        )
        next = request.query_params.get('next', '/apps')
        return RedirectResponse(url=request.url.path, status_code=302)
    if request.method == 'POST' and form.validate():
        _client = OAuth2Client.objects.create(
            OAuth2ClientCreate(user=request.user, **data))
        next = request.query_params.get('next', '/apps')
        return RedirectResponse(url=next, status_code=302)
    clients = OAuth2Client.objects.fetch_for_user(request.user)
    return render('clients.html', {
        'form': form,
        'api_clients': clients
    })
