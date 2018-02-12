import jwt
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils.six import text_type
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from rest_framework import HTTP_HEADER_ENCODING
from rest_framework import authentication, exceptions
from jwt_auth.models import Staff
from rest_framework.authentication import (
    BaseAuthentication, get_authorization_header
)
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER
jwt_get_user_id_from_payload = api_settings.JWT_PAYLOAD_GET_USER_ID_HANDLER

class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'session'), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE%s setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        ) % ("_CLASSES" if settings.MIDDLEWARE is None else "")
        request.user = JWTAuth.get_user_from_request(request)
        #request.user = Staff.objects.get(username='admin')

class JWTAuth:
    @classmethod
    def _check_payload(cls, token):
        # Check payload valid (based off of JSONWebTokenAuthentication,
        # may want to refactor)
        try:
            payload = jwt_decode_handler(token)
        except jwt.ExpiredSignature:
            msg = 'Signature has expired.'
            raise ValueError(msg)
        except jwt.DecodeError:
            msg = 'Error decoding signature.'
            raise ValueError(msg)
        return payload

    @classmethod
    def _check_user(cls, payload):
        user_id = jwt_get_user_id_from_payload(payload)

        if not user_id:
            msg = 'Invalid payload.'
            raise ValueError(msg)

        user_id = int(user_id)

        # Make sure user exists
        try:
            user = Staff.objects.get(id=user_id)
        except:
            msg = "User doesn't exist."
            raise ValueError(msg)

        if not user.is_active:
            msg = 'User account is disabled.'
            raise ValueError(msg)

        return user

    @classmethod
    def get_user_from_request(cls, request):
        try:
            auth_cookie = request.COOKIES.get(settings.JWT_AUTH['JWT_AUTH_COOKIE'], '')
            payload = cls._check_payload(auth_cookie)
            user = cls._check_user(payload)
            return user
        except:
            return AnonymousUser()