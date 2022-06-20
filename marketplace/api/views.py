from datetime import timedelta

from django.db import transaction
from django.http import Http404
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .models import Item, ItemArchiveVersions
from .serializers import (DeleteItemSerializer, GetItemSerializer,
                          ItemStatisticSerializer, PutItemSerializer,
                          SalesItemSerializer)
from .tasks import save_archive_versions
from .utils import (ChangedListAPIView, ChangedRetrieveAPIView,
                    ItemNotInDBError, avg_children_price_and_date,
                    uuid_validate, validate_date, request_data_validate, )


class GetItemAPIView(ChangedRetrieveAPIView):
    http_method_names = ['get']
    queryset = Item.objects.all()
    serializer_class = GetItemSerializer
    throttle_scope = 'contacts'

    def retrieve(self, request, *args, **kwargs):
        if not uuid_validate(kwargs.get('pk')):
            raise serializers.ValidationError
        instance = self.get_object()
        if instance.type == 'OFFER':
            instance.children = None
            descendants_dict = None

        else:
            instance.price, instance.date = avg_children_price_and_date(
                instance
            )
            descendants_dict = {str(d): d for d in instance.get_descendants()}
        serializer = self.get_serializer(instance)
        serializer_data = serializer.data
        serializer_data['date'] = validate_date(
            serializer_data['date']
        ).isoformat(sep='T', timespec='milliseconds') + 'Z'
        self.get_all_children(serializer_data, descendants_dict)
        return Response(serializer_data)


class PostItemAPIView(generics.CreateAPIView):
    http_method_names = ['post']
    queryset = Item.objects.all()
    serializer_class = PutItemSerializer
    throttle_scope = 'uploads'

    def create(self, request, *args, **kwargs):
        if not isinstance(request.data, dict):
            raise serializers.ValidationError
        request_list, items_id_list, parents_in_db_id_dict = \
            request_data_validate(request.data)
        items_in_db_dict = {
            str(i): i for i in Item.objects.filter(id__in=items_id_list)
        }
        step = 0
        with transaction.atomic():
            while len(request_list) > 0:
                try:
                    # проверяем валидность Item, контолируем поведение, если
                    # родитель находится в запросе, а не в базе данных
                    item = request_list[step]
                    try:
                        current_item = items_in_db_dict[item['id']]
                    except KeyError:
                        current_item = None
                    if not current_item:
                        serializer = self.get_serializer(data=item)
                        serializer.is_valid(raise_exception=True)
                    else:
                        serializer = self.get_serializer(
                            current_item, data=item
                        )
                        serializer.is_valid(raise_exception=True)

                    try:
                        # Проверяем должен ли у Item быть родитель, если нет -
                        # создаём, инчае, если родитель ещё не создан,
                        # выбрасываем контролируемую ошибку
                        if not item.get('parent'):
                            parent = None
                        else:
                            parent = parents_in_db_id_dict[item.get('parent')]
                            if parent.type != 'CATEGORY':
                                raise serializers.ValidationError
                        fresh_item = self.perform_create(serializer, parent)
                        parents_in_db_id_dict[str(fresh_item)] = fresh_item
                        request_list.remove(item)
                        step = 0
                    except KeyError:
                        raise ItemNotInDBError
                except ItemNotInDBError:
                    step += 1
                except Exception:
                    raise serializers.ValidationError

        # Созаём архивные версии категорий, затронутых текущим запросом
        save_archive_versions.delay(items_id_list)
        return Response(status=HTTP_200_OK)

    def perform_create(self, serializer, parent):
        fresh_item = serializer.save(parent=parent)
        return fresh_item


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
