from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied,
    ValidationError as DjangoValidationError,
)
from django.db import IntegrityError, DatabaseError
from django.http import Http404
from rest_framework.exceptions import (
    NotFound,
    MethodNotAllowed,
    Throttled,
    ValidationError,
    AuthenticationFailed,
)
import requests.exceptions


def custom_exception_handler(exc, context):

    if isinstance(exc, ObjectDoesNotExist):
        custom_response = {
            "status": False,
            "code": status.HTTP_404_NOT_FOUND,
            "message": "The requested resource was not found.",
        }
        return Response(custom_response, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, Http404):
        custom_response = {
            "status": False,
            "code": status.HTTP_404_NOT_FOUND,
            "message": "The requested URL was not found on this server.",
        }
        return Response(custom_response, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, MethodNotAllowed):
        custom_response = {
            "status": False,
            "code": status.HTTP_405_METHOD_NOT_ALLOWED,
            "message": "This method is not allowed for the requested URL.",
        }
        return Response(custom_response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if isinstance(exc, Throttled):
        custom_response = {
            "status": False,
            "code": status.HTTP_429_TOO_MANY_REQUESTS,
            "message": "Too many requests. Please try again later.",
        }
        return Response(custom_response, status=status.HTTP_429_TOO_MANY_REQUESTS)

    if isinstance(exc, ValidationError):
        custom_response = {
            "status": False,
            "code": status.HTTP_400_BAD_REQUEST,
            "message": exc.detail,
        }
        return Response(custom_response, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, DjangoValidationError):
        custom_response = {
            "status": False,
            "code": status.HTTP_400_BAD_REQUEST,
            "message": exc.message_dict,
        }
        return Response(custom_response, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, AuthenticationFailed):
        custom_response = {
            "status": False,
            "code": status.HTTP_401_UNAUTHORIZED,
            "message": "Authentication failed.",
        }
        return Response(custom_response, status=status.HTTP_401_UNAUTHORIZED)

    if isinstance(exc, PermissionDenied):
        custom_response = {
            "status": False,
            "code": status.HTTP_403_FORBIDDEN,
            "message": "You do not have permission to perform this action.",
        }
        return Response(custom_response, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, IntegrityError):
        custom_response = {
            "status": False,
            "code": status.HTTP_400_BAD_REQUEST,
            "message": "A database integrity error occurred.",
        }
        return Response(custom_response, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, DatabaseError):
        custom_response = {
            "status": False,
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "A database error occurred.",
        }
        return Response(custom_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if isinstance(exc, requests.exceptions.ConnectionError):
        custom_response = {
            "status": False,
            "code": status.HTTP_503_SERVICE_UNAVAILABLE,
            "message": "A network error occurred. Please check your connection and try again.",
        }
        return Response(custom_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    if isinstance(exc, requests.exceptions.Timeout):
        custom_response = {
            "status": False,
            "code": status.HTTP_504_GATEWAY_TIMEOUT,
            "message": "The request timed out. Please try again later.",
        }
        return Response(custom_response, status=status.HTTP_504_GATEWAY_TIMEOUT)

    if isinstance(exc, requests.exceptions.RequestException):
        custom_response = {
            "status": False,
            "code": status.HTTP_502_BAD_GATEWAY,
            "message": "A network error occurred. Please try again later.",
        }
        return Response(custom_response, status=status.HTTP_502_BAD_GATEWAY)

    custom_response = {
        "status": False,
        "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "message": "An unexpected error occurred. Please try again later.",
    }
    return Response(custom_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
