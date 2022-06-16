import re
from datetime import datetime

from django.http import Http404
from rest_framework import generics, serializers
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
    if parent.type == 'CATEGORY':
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


def request_data_validate(request_data):
    """
    Функция нормализует данные полученные из Request.data, и проверяет, что
    родитель каждого Item находится либо в БД, либо в текущем запросе,
    функция возвращает список нормализованных Items.
    """
    if (not request_data.get('items')) or not (request_data.get('updateDate')):
        raise serializers.ValidationError
    items_id_list = []
    items_parent_id_set = set()
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
        parents_in_db = Item.objects.filter(
            pk__in=items_parent_id_set
        ).values_list('id')
        parents_in_db_id_set = {str(p[0]) for p in parents_in_db}

        for parent_id in items_parent_id_set:
            if (parent_id not in parents_in_db_id_set
                    and parent_id not in items_id_set):
                raise serializers.ValidationError
    return request_data['items'], items_id_set


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
        serializer_data = serializer.data
        for item in serializer_data:
            item['date'] = validate_date(
                    item['date']
                ).isoformat(sep='T', timespec='milliseconds') + 'Z'
        return Response(data={"items": serializer_data})


class ChangedRetrieveAPIView(generics.RetrieveAPIView):

    def get_all_children(self, data, descendants):
        """
        Рекурсивная функция распаковывающая детей
        у сериализованного объекта Item.
        """
        if data.get('children'):
            step = 0
            while step < len(data.get('children')):
                item = descendants.get(id=data.get('children')[step])
                if not item.price:
                    item.price, item.date = avg_children_price_and_date(item)
                child = self.get_serializer(item).data
                child['date'] = validate_date(
                    child['date']
                ).isoformat(sep='T', timespec='milliseconds') + 'Z'
                data.get('children')[step] = child
                self.get_all_children(child, descendants)
                step += 1
        elif data['type'] == 'OFFER':
            data['children'] = None


class ItemNotInDBError(Exception):
    pass
