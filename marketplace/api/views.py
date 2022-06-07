from datetime import datetime, timedelta

from django.http import Http404
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .models import Item, ItemOldVersions
from .utils import ChangedListAPIView, uuid_validate
from .serializers import (DeleteItemSerializer, GetItemSerializer,
                          ItemStatisticSerializer, PutItemSerializer,
                          SalesItemSerializer)


class GetItemAPIView(generics.RetrieveAPIView):
    http_method_names = ['get']
    queryset = Item.objects.all()
    serializer_class = GetItemSerializer
    throttle_scope = 'contacts'

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

    def retrieve(self, request, *args, **kwargs):
        if not uuid_validate(kwargs.get('pk')):
            raise serializers.ValidationError
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        self.get_all_children(serializer.data)
        return Response(serializer.data)


class PutItemAPIView(generics.CreateAPIView, generics.UpdateAPIView):
    http_method_names = ['post']
    queryset = Item.objects.all()
    serializer_class = PutItemSerializer
    throttle_scope = 'uploads'

    def create(self, request, *args, **kwargs):
        if (not request.data.get('items')) or not (
                request.data.get('updateDate')
        ):
            raise serializers.ValidationError

        for item in request.data['items']:
            # Проверяем что parentID у всех итемов в запросе либо в базе,
            # либо в текущем запросе, либо отсутствует, иначе ValidationError
            if (item.get('parentId') and item.get('parentId') != "Null"
                    and item.get('parentId') != "None"):
                parent_in_db = Item.objects.filter(pk=item['parentId']).first()
                if not parent_in_db:
                    flag = False
                    for another_item in request.data['items']:
                        if ((another_item['id'] == item['parentId'])
                                and (another_item['type'] == 'CATEGORY')):
                            flag = True
                            break
                    if not flag:
                        raise serializers.ValidationError
        ## по условию задачи итемы идут неупорядачено, то есть мне нельзя
        ## создавать их по очереди, нужно создавать только если нет родителя
        ## или он уже в базе
        for item in request.data['items']:
            item['date'] = request.data['updateDate']
            # Удаляем атрибут price из входных данных если он не определён
            if 'price' in item.keys():
                price = item.get('price')
                if (not price) or (price == "None") or (price == "Null"):
                    item.pop('price')
            # Добавляем ключ parent если он определён
            if 'parentId' in item.keys():
                parent = item.get('parentId')
                if parent and (parent not in ("None", "Null")):
                    item['parent'] = parent
            # Если объект уже существует: редактируем, иначе создаём
            current_item = Item.objects.filter(pk=item['id']).first()
            if not current_item:
                serializer = self.get_serializer(data=item)
            else:
                instance = current_item
                serializer = self.get_serializer(instance, data=item)
                ## не понимаю что делают эти строчки, может их можно удалить?
                if getattr(instance, '_prefetched_objects_cache', None):
                    instance._prefetched_objects_cache = {}

            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        ## если вот тут вызывать функцию, которая будет перерасчитывать
        ## цену категории, то это может сильно сократить нагрузу на БД
        ## т.к сигналы вызваются при добавлении каждого объекта.
        return Response(status=HTTP_200_OK)


class DeleteItemAPIView(generics.DestroyAPIView):
    queryset = Item.objects.all()
    serializer_class = DeleteItemSerializer
    throttle_scope = 'uploads'

    def destroy(self, request, *args, **kwargs):
        if not uuid_validate(kwargs.get('pk')):
            raise serializers.ValidationError
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=HTTP_200_OK)


class SalesItemAPIView(ChangedListAPIView):
    serializer_class = SalesItemSerializer
    throttle_scope = 'contacts'

    def get_queryset(self):
        end_date = self.request.query_params.get('date')
        if not end_date:
            raise serializers.ValidationError
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ')
            except:
                raise serializers.ValidationError
        start_date = end_date - timedelta(days=1)
        queryset = Item.objects.filter(
            type='OFFER', date__range=(start_date, end_date)
        )
        return queryset


class ItemStatisticAPIView(ChangedListAPIView):
    serializer_class = ItemStatisticSerializer
    throttle_scope = 'contacts'

    def get_queryset(self):
        if not self.kwargs.get('pk'):
            raise serializers.ValidationError
        if not uuid_validate(self.kwargs.get('pk')):
            raise serializers.ValidationError
        queryset = ItemOldVersions.objects.filter(
            actual_version=str(self.kwargs.get('pk'))
        )
        if not queryset:
            raise Http404
        return queryset
