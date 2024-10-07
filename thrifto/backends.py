# yourapp/backends.py
from django.contrib.auth.backends import ModelBackend
from .models import UserProfile

class EmailBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        UserModel = UserProfile
        try:
            email = kwargs.get('email', None)
            if email is None:
                email = kwargs.get('username', None)
            user = UserModel.objects.get(email=email)
            if user.check_password(kwargs.get('password', None)):
                return user
        except UserModel.DoesNotExist:
            return None
        return None