import re

from django.http import Http404
from rest_framework import generics
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
    ## ощущение что Гвиде ван руссом не одобрит, но 79 символов карл
    if not (
        re.match(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            string
        )
    ):
        return False
    return True


class ChangedListAPIView(generics.ListAPIView):

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(data={"items": serializer.data})


class ItemNotInDBError(Exception):
    pass
