from datetime import datetime, timedelta

from django.http import Http404
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .models import Item, ItemOldVersions
from .serializers import (DeleteItemSerializer, GetItemSerializer,
                          PutItemSerializer, SalesItemSerializer,
                          ItemStatisticSerializer,)


class GetItemAPIView(generics.RetrieveAPIView):
    http_method_names = ['get']
    queryset = Item.objects.all()
    serializer_class = GetItemSerializer

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
        if len(kwargs.get('pk')) != 36:
            raise serializers.ValidationError
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        self.get_all_children(serializer.data)
        return Response(serializer.data)


class PutItemAPIView(generics.CreateAPIView, generics.UpdateAPIView):
    http_method_names = ['post']
    queryset = Item.objects.all()
    serializer_class = PutItemSerializer

    def create(self, request, *args, **kwargs):
        if (not request.data.get('items')) or not (
                request.data.get('updateDate')
        ):
            raise serializers.ValidationError

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
                    item['parent'] = item['parentId']
            # Если объект уже существует: редактируем, иначе создаём
            current_item = Item.objects.filter(pk=item['id']).first()
            if not current_item:
                serializer = self.get_serializer(data=item)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
            else:
                instance = current_item
                serializer = self.get_serializer(instance, data=item)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)

                if getattr(instance, '_prefetched_objects_cache', None):
                    instance._prefetched_objects_cache = {}
        return Response(status=HTTP_200_OK)


class DeleteItemAPIView(generics.DestroyAPIView):
    queryset = Item.objects.all()
    serializer_class = DeleteItemSerializer

    def destroy(self, request, *args, **kwargs):
        if len(kwargs.get('pk')) != 36:
            raise serializers.ValidationError
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=HTTP_200_OK)


class SalesItemAPIView(generics.ListAPIView):
    serializer_class = SalesItemSerializer

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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(data={"items": serializer.data})


class ItemStatisticAPIView(generics.ListAPIView):
    serializer_class = ItemStatisticSerializer

    def get_queryset(self):
        if not self.kwargs.get('pk'):
            raise serializers.ValidationError
        if len(self.kwargs.get('pk')) != 36:
            raise serializers.ValidationError
        queryset = ItemOldVersions.objects.filter(
            actual_version=str(self.kwargs.get('pk'))
        )
        if not queryset:
            raise Http404
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(data={"items": serializer.data})
