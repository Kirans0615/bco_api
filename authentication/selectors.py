# authentication/selectors.py

import jwt
from django.conf import settings
from django.contrib.auth.models import User, Permission
from authentication.models import Authentication, NewUser
from rest_framework.authtoken.models import Token
from prefix.selectors import get_user_prefixes
from biocompute.selectors import get_authorized_bcos

def get_anon()-> User:
    """Get AnonymosUser
    """
    return User.objects.get(username="AnonymousUser")

def get_user_from_auth_token(token: str)-> User:
    """Get user from Auth Token
    """
    payload = jwt.decode(token, None, False)

    if payload['iss'] == 'https://orcid.org' or payload['iss'] == 'https://sandbox.orcid.org':
        try:
            return User.objects.get(username=Authentication.objects.get(auth_service__icontains=payload['sub']).username)
        except User.DoesNotExist:
            return None
    if payload['iss'] == 'accounts.google.com':
        try:
            return User.objects.get(email=payload['email'])
        except User.DoesNotExist:
            return None
    if payload['iss'] in ['http://localhost:8080', 'https://test.portal.biochemistry.gwu.edu/', 'https://biocomputeobject.org/']:
        try:
            return User.objects.get(email=payload['email'])
        except User.DoesNotExist:
            return None

def check_user_email(email: str)-> bool:
    """Check for user

    Using the provided email check for a user in the DB
    """

    try:
        if User.objects.get(email=email):
            return True
    except User.DoesNotExist:
        return False

def check_new_user(email: str) -> bool:
    """Check for new user

    Using the provided email check for a new user in the DB.
    """
    
    try:
        NewUser.objects.get(email=email)
        return True
    except NewUser.DoesNotExist:
        return False

def get_user_info(user: User) -> dict:
    """Get User Info

        Arguments
        ---------
        user:  the user object.

        Returns
        -------
        A dict with the user information.
    """

    token = Token.objects.get(user=user.pk)
    other_info = {
        "permissions": {},
        "account_creation": "",
    }
    user_perms = {"prefixes": get_user_prefixes(user), "BCOs": get_authorized_bcos(user)}

    other_info["permissions"] = user_perms

    other_info["account_creation"] = user.date_joined

    return {
        "hostname": settings.HOSTNAME,
        "human_readable_hostname": settings.HUMAN_READABLE_HOSTNAME,
        "public_hostname": settings.PUBLIC_HOSTNAME,
        "token": token.key,
        "username": user.username,
        "other_info": other_info,
    }