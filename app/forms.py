from datetime import timedelta
from wtforms import Form, BooleanField, StringField, validators, PasswordField, HiddenField
from wtforms.csrf.session import SessionCSRF
from .config import settings
from .orm.oauth2client import OAuth2Client
from .orm.user import User


class CSRFForm(Form):

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = settings.CSRF_KEY.encode()
        csrf_time_limit = timedelta(minutes=20)


class LoginForm(CSRFForm):
    email = StringField('Email address', [validators.Email()])
    password = PasswordField('Password')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def validate_password(form, field):
        _user = User.objects.authenticate(
            email=form.email.data,
            password=field.data
        )
        if _user is None:
            raise validators.ValidationError('Incorrect email or password')
        elif not _user.is_active:
            raise validators.ValidationError(
                'This account has been administratively deactivated. '\
                'Please contact technical support.')
        form.user = _user

    def validate(self):
        super().validate()
        return self.user   


class PublicUserForm(CSRFForm):
    full_name = StringField('Full name')
    email = StringField('Email address', [validators.Email()])

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def validate_is_superuser(form, field):
        if not form.request.user.is_superuser:
            raise HTTPException(403, 'Not authorized')


class AdminUserForm(PublicUserForm):
    is_superuser = BooleanField('Superuser')


def UserForm(request, *args, **kwargs):
    """Factory that returns the correct user form."""
    if request.user.is_superuser:
        return AdminUserForm(request, *args, **kwargs)
    else:
        return PublicUserForm(request, *args, **kwargs)


class PasswordResetForm(CSRFForm):
    token = HiddenField()
    new_password = PasswordField('New password')
    retype_password = PasswordField('Retype new password')
        
    def validate_retype_password(form, field):
        if field.data != form.new_password.data:
            raise validators.ValidationError('Passwords must match')


class PasswordForm(CSRFForm):
    current_password = PasswordField('Current password')
    new_password = PasswordField('New password')
    retype_password = PasswordField('Retype new password')
        
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def validate_current_password(form, field):
        if not form.user.verify_user_password(field.data):
            raise validators.ValidationError('Incorrect password')

    def validate_retype_password(form, field):
        if field.data != form.new_password.data:
            raise validators.ValidationError('Passwords must match')


class APIClientForm(CSRFForm):
    name = StringField('Name')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def validate_name(self, field):
        exists = OAuth2Client.objects.exists(self.request.user, field.data) 
        if exists:
            raise validators.ValidationError(
                'Unique application name required.')

