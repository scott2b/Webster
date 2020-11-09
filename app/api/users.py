from spectree import Response
from starlette.authentication import requires
from starlette.responses import JSONResponse
from ..orm.user import User, UserProfileResponse
from ..schemas.user import UserUpdateRequest, UserPasswordUpdateRequest
from . import _app, APIExceptionResponse, APIMessage
from . import ValidationErrorList
from pydantic import ValidationError


@requires('api_auth', status_code=401)
@_app.validate(json=UserUpdateRequest,
               resp=Response(HTTP_200=UserProfileResponse,
                             HTTP_401=APIExceptionResponse,
                             HTTP_422=ValidationErrorList), tags=['user'])
async def profile(request):
    user=request.scope['token'].get_user()
    if request.method == 'PUT':
        data = await request.json()
        obj = UserUpdateRequest(**data)
        User.objects.update(db_obj=user, obj_in=obj)
    return JSONResponse(user.dict(model=UserProfileResponse), status_code=200)



@requires('api_auth', status_code=401)
@_app.validate(json=UserUpdateRequest,
               resp=Response(HTTP_200=APIMessage,
                             HTTP_401=APIExceptionResponse,
                             HTTP_422=ValidationErrorList), tags=['user'])
async def password(request):
    user=request.scope['token'].get_user()
    data = await request.json()
    obj = UserPasswordUpdateRequest(**data)
    User.objects.update(db_obj=user, obj_in=obj)
    return JSONResponse(
        APIMessage(msg='Updated', status=200).dict(),
        status_code=200)
