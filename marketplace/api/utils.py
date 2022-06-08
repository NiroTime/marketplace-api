import logging
import re

from django.http import Http404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .models import Item


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


def avg_children_price(parent):
    """
    Функция принимает на вход родителя, считает сумарную стоимость
    и количество детей, возвращает среднюю стоимость или None, если
    у категории нет детей с типом OFFER.
    """
    try:
        children = parent.get_descendants()
    except Exception as err:
        logging.error(f'ошибка:{err}')
        children = None
    if children:
        all_offers_price = 0
        offers_count = 0
        for item in children:
            if item.type == 'OFFER':
                all_offers_price += item.price
                offers_count += 1
        try:
            return all_offers_price // offers_count
        except ZeroDivisionError:
            return None
    return None


class ChangedListAPIView(generics.ListAPIView):

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(data={"items": serializer.data})


class ChangedRetrieveAPIView(generics.RetrieveAPIView):

    def get_all_children(self, data):
        """
        Рекурсивная функция распаковывающая детей
        у сериализованного объекта Item.
        """
        if data.get('children'):
            step = 0
            while step < len(data.get('children')):
                item = Item.objects.filter(
                    pk=data.get('children')[step]).first()
                child = self.get_serializer(item).data
                data.get('children')[step] = child
                self.get_all_children(child)
                step += 1


class ItemNotInDBError(Exception):
    pass
