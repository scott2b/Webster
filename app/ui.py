from .orm import oauth2, user
from .orm.db import db_session
from starlette.exceptions import HTTPException
from starlette.templating import Jinja2Templates
from starlette.responses import PlainTextResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session


templates = Jinja2Templates(directory='templates')


def logout(request):
    del request.session['username']
    return RedirectResponse(url='/')


@db_session
async def homepage(request, db:Session):
    if request.method == 'POST':
        form = await request.form()
        _user = user.users.authenticate(
            email=form['username'],
            password=form['password'],
            db=db
        )
        if not _user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        elif not user.users.is_active(_user):
            raise HTTPException(status_code=400, detail="Inactive user")
        request.session['username'] = form['username']
    return templates.TemplateResponse('home.html', {'request': request})
