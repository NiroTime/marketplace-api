import re

from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Кастомизируем ответ клиенту в соответсвии с ТЗ."""
    if isinstance(exc, ValidationError):
        data = {
            "code": 400,
            "message": "Validation Failed"
        }
        return Response(status=400, data=data)
    if isinstance(exc, Http404):
        data = {
            "code": 404,
            "message": "Item not found"
        }
        return Response(status=404, data=data)
    response = exception_handler(exc, context)
    return response


def uuid_validate(string):
    if not (
        re.match(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            string
        )
    ):
        return False
    return True
