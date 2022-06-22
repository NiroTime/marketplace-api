import re
from datetime import datetime

from django.db.models import Avg, Max
from django.http import Http404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .models import Item, ItemArchiveVersions


def validate_date(date):
    """Функция валидирует дату, и возвращает объект datetime или False."""
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
    """Кастомизируем ответ клиенту."""
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
    """Функция валидирует uuid, возвращает True или False."""
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
    price = parent.get_descendants().filter(
        type='OFFER'
    ).aggregate(Avg('price'))
    date = parent.get_descendants(include_self=True).aggregate(Max('date'))
    if price['price__avg']:
        return int(price['price__avg']), date['date__max']
    return None, date['date__max']


def request_data_validate(request_data):
    """
    Функция нормализует данные полученные из Request.data, и проверяет, что
    родитель каждого Item находится либо в БД, либо в текущем запросе,
    функция возвращает список нормализованных items, список items id,
    а так же словарь родителей items, уже сохранённых в БД,вида item.id: item.
    """
    if (not request_data.get('items')) or not (request_data.get('updateDate')):
        raise serializers.ValidationError
    items_id_list = []
    items_parent_id_set = set()
    parents_in_db_id_dict = {}
    for item in request_data['items']:
        items_id_list.append(item.get('id'))
        item['date'] = request_data['updateDate']
        # Удаляем атрибут price из входных данных если он не определён
        if 'price' in item.keys() and not item.get('price'):
            item.pop('price')
        # Добавляем ключ parent если он определён
        if 'parentId' in item.keys() and item.get('parentId'):
            item['parent'] = item.get('parentId')
        # Проверяем что parentId отличается от id
        if item.get('parent'):
            if not uuid_validate(item.get('parent')) or (
                    item.get('id') == item.get('parent')):
                raise serializers.ValidationError
            items_parent_id_set.add(item.get('parent'))

    # В запросе не должно быть Items с одинаковым id
    items_id_set = set(items_id_list)
    if len(items_id_list) != len(items_id_set):
        raise serializers.ValidationError

    # Убедимся, что родители всех Items находятся либо в БД, либо в запросе
    if items_parent_id_set:
        parents_in_db_id_dict = {
            str(p): p for p in Item.objects.filter(pk__in=items_parent_id_set)
        }

        for parent_id in items_parent_id_set:
            if (parent_id not in set(parents_in_db_id_dict.keys())
                    and parent_id not in items_id_set):
                raise serializers.ValidationError
    return request_data['items'], items_id_list, parents_in_db_id_dict


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


class ItemNotInDBError(Exception):
    pass
