from datetime import timedelta

from django.http import Http404
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .models import Item, ItemArchiveVersions
from .serializers import (DeleteItemSerializer, GetItemSerializer,
                          ItemStatisticSerializer, PutItemSerializer,
                          SalesItemSerializer)
from .signals import create_item_archive_version
from .utils import (ChangedListAPIView, ChangedRetrieveAPIView,
                    ItemNotInDBError, avg_children_price, uuid_validate,
                    validate_date)


class GetItemAPIView(ChangedRetrieveAPIView):
    http_method_names = ['get']
    queryset = Item.objects.all()
    serializer_class = GetItemSerializer
    throttle_scope = 'contacts'

    def retrieve(self, request, *args, **kwargs):
        if not uuid_validate(kwargs.get('pk')):
            raise serializers.ValidationError
        instance = self.get_object()
        if not instance.children:
            instance.children = None
        if not instance.price:
            instance.price, instance.date = avg_children_price(instance)
        serializer = self.get_serializer(instance)
        serializer_data = serializer.data
        serializer_data['date'] = validate_date(
            serializer_data['date']
        ).isoformat(sep='T', timespec='milliseconds') + 'Z'
        self.get_all_children(serializer_data)
        return Response(serializer_data)


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
            item['date'] = request.data['updateDate']
            # Удаляем атрибут price из входных данных если он не определён
            if 'price' in item.keys():
                if not item.get('price'):
                    item.pop('price')
            # Добавляем ключ parent если он определён
            if 'parentId' in item.keys():
                if item.get('parentId'):
                    item['parent'] = item.get('parentId')
            # Проверяем что parentID у всех итемов в запросе либо в базе,
            # либо в текущем запросе, либо отсутствует, иначе ValidationError
            if item.get('parent'):
                if not uuid_validate(item.get('parent')):
                    raise serializers.ValidationError
                parent_in_db = Item.objects.filter(pk=item['parent']).first()
                if not parent_in_db:
                    flag = False
                    for another_item in request.data['items']:
                        if ((another_item['id'] == item['parent'])
                                and (another_item['type'] == 'CATEGORY')):
                            flag = True
                            break
                    if not flag:
                        raise serializers.ValidationError
                else:
                    if parent_in_db.type != 'CATEGORY':
                        raise serializers.ValidationError

        request_list = list(request.data['items'])
        step = 0
        temp_data = []
        while len(request_list) > 0:
            try:
                # проверяем валидность Item, контолируем поведение, если
                # родитель находится в запросе, а не в базе данных
                item = request_list[step]
                current_item = Item.objects.filter(pk=item['id']).first()
                if not current_item:
                    serializer = self.get_serializer(data=item)
                    serializer.is_valid(raise_exception=True)
                    method = 'POST'
                else:
                    instance = current_item
                    serializer = self.get_serializer(instance, data=item)
                    serializer.is_valid(raise_exception=True)
                    method = 'PUT'

                try:
                    # Проверяем должен ли у Item быть родитель, если нет -
                    # создаём, инчае, если родитель ещё не создан, выбрасываем
                    # контролируемую ошибку
                    if not item.get('parent'):
                        parent = None
                    else:
                        parent = Item.objects.get(pk=item.get('parent'))
                    self.perform_create(serializer, parent)
                    temp_data.append(serializer.validated_data.get('id'))
                    request_list.remove(item)
                    step = 0
                    if method == 'PUT':
                        if getattr(
                                instance, '_prefetched_objects_cache', None
                        ):
                            instance._prefetched_objects_cache = {}
                except Exception:
                    raise ItemNotInDBError
            except ItemNotInDBError:
                step += 1
            except Exception:
                for item_id in temp_data:
                    item = Item.objects.get(pk=item_id)
                    item.delete()
                raise serializers.ValidationError

        # Созаём архивные версии категорий, затронутых текущим запросом
        ancestors = []
        for item_id in temp_data:
            item = Item.objects.filter(pk=item_id)
            ancestors += item.get_ancestors()
        for item in set(ancestors):
            create_item_archive_version(instance=item)

        return Response(status=HTTP_200_OK)

    def perform_create(self, serializer, parent):
        serializer.save(parent=parent)


class DeleteItemAPIView(generics.DestroyAPIView):
    queryset = Item.objects.all()
    serializer_class = DeleteItemSerializer
    throttle_scope = 'uploads'

    def destroy(self, request, *args, **kwargs):
        if not uuid_validate(kwargs.get('pk')):
            raise serializers.ValidationError
        instance = self.get_object()
        ancestors = instance.get_ancestors()
        self.perform_destroy(instance)
        for item in ancestors:
            item.date = timezone.now()
            item.save()
        return Response(status=HTTP_200_OK)


class SalesItemAPIView(ChangedListAPIView):
    http_method_names = ['get']
    serializer_class = SalesItemSerializer
    throttle_scope = 'contacts'

    def get_queryset(self):
        end_date = self.request.query_params.get('date')
        if not end_date:
            raise serializers.ValidationError
        end_date = validate_date(end_date)
        if not end_date:
            raise serializers.ValidationError
        start_date = end_date - timedelta(days=1)
        queryset = Item.objects.filter(
            type='OFFER', date__range=(start_date, end_date)
        )
        if not queryset:
            raise Http404
        return queryset


class ItemStatisticAPIView(ChangedListAPIView):
    http_method_names = ['get']
    serializer_class = ItemStatisticSerializer
    throttle_scope = 'contacts'

    def get_queryset(self):
        if not self.kwargs.get('pk'):
            raise serializers.ValidationError
        if not uuid_validate(self.kwargs.get('pk')):
            raise serializers.ValidationError
        start_date = validate_date(self.request.query_params.get('dateStart'))
        end_date = validate_date(self.request.query_params.get('dateEnd'))
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError
        if start_date and end_date:
            queryset = ItemArchiveVersions.objects.filter(
                actual_version=str(self.kwargs.get('pk')),
                date__range=(start_date, end_date),
            )
        elif start_date:
            queryset = ItemArchiveVersions.objects.filter(
                actual_version=str(self.kwargs.get('pk')),
                date__gte=start_date,
            )
        elif end_date:
            queryset = ItemArchiveVersions.objects.filter(
                actual_version=str(self.kwargs.get('pk')),
                date__lte=end_date,
            )
        else:
            queryset = ItemArchiveVersions.objects.filter(
                actual_version=str(self.kwargs.get('pk'))
            )

        if not queryset:
            raise Http404
        return queryset
