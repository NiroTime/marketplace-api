import re
from datetime import datetime

from django.http import Http404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .models import Item


def validate_date(date):
    try:
        validated_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        return validated_date
    except:
        try:
            validated_date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
            return validated_date
        except:
            return False


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
    children = parent.get_descendants()
    if children:
        all_offers_price = 0
        offers_count = 0
        last_update = parent.date
        for item in children:
            if item.type == 'OFFER':
                all_offers_price += item.price
                offers_count += 1
            if item.date > last_update:
                last_update = item.date
        try:
            return all_offers_price // offers_count, last_update
        except ZeroDivisionError:
            return None, parent.date
    return None, parent.date


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
                if not item.price:
                    item.price, item.date = avg_children_price(item)
                child = self.get_serializer(item).data
                child['date'] = validate_date(
                    child['date']
                ).isoformat(sep='T', timespec='milliseconds') + 'Z'
                data.get('children')[step] = child
                self.get_all_children(child)
                step += 1
        else:
            data['children'] = None


class ItemNotInDBError(Exception):
    pass
