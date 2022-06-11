import re
from datetime import datetime

from django.http import Http404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .models import Item, ItemArchiveVersions


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


def avg_children_price_and_date(parent):
    """
    Функция принимает на вход родителя, считает среднюю стоимость категории,
    а так же ищет последнюю дату обновления, возвращает среднюю стоимость
    или None, если у категории нет детей с типом OFFER, и последнюю дату
    обновления.
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


def create_item_archive_version(instance):
    """
    Функция создаёт архинвую версию товара/категории.
    """
    fresh_archive_version = ItemArchiveVersions(
        actual_version=str(instance.id),
        name=instance.name,
        price=instance.price,
        date=instance.date,
        type=instance.type,
        parent=str(instance.parent),
    )
    if instance.type == 'CATEGORY':
        fresh_archive_version.price, date = avg_children_price_and_date(
            instance
        )
        if fresh_archive_version.date < date:
            fresh_archive_version.date = date
    return fresh_archive_version


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
                    item.price, item.date = avg_children_price_and_date(item)
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
