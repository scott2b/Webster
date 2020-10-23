from pydantic import BaseModel, Field, constr
from spectree import SpecTree, Response
from spectree.plugins.starlette_plugin import StarlettePlugin, PAGES
from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

UI_ROUTES = {
  'redoc': 'api',
  'swagger': 'swagger'
}

class CustomPlugin(StarlettePlugin):

    def register_route(self, app):
        self.app = app
        try:
            self.app.add_route(
                self.config.spec_url,
                lambda request: JSONResponse(self.spectree.spec),
            )
        except: # wtf?
            pass
        for ui in PAGES:
            self.app.add_route(
                f'/{self.config.PATH}/{UI_ROUTES[ui]}',
                lambda request, ui=ui: HTMLResponse(
                    PAGES[ui].format(self.config.spec_url)
                ),
            )

api = SpecTree('starlette', path='docs', backend=CustomPlugin, MODE='strict')
# api = SpecTree('starlette', path='docs', MODE='strict')


class Message(BaseModel):
    text: str


class Profile(BaseModel):
    name: constr(min_length=2, max_length=40)  # Constrained Str
    age: int = Field(
        ...,
        gt=0,
        lt=150,
        description='user age(Human)'
    )


@api.validate(json=Profile, resp=Response(HTTP_200=Message, HTTP_403=None), tags=['api'])
@requires('authenticated', status_code=403)
async def user_profile(request):
    """
    verify user profile (summary of this endpoint)

    user's name, user's age, ... (long description)
    """
    print(request.context.json)  # or await request.json()
    return JSONResponse({'text': 'it works'})


routes = [
    Route('/user', user_profile, methods=['POST']),
]

app = Starlette(
    debug=True,
    routes=routes,
    on_startup=[])


api.register(app)
