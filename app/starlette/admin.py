from starlette.authentication import requires
from .templates import render


@requires('admin_auth', status_code=403)
async def admin(request):
    return render('admin.html', {})
