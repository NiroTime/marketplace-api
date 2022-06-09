from datetime import timedelta

from django.http import Http404
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .models import Item, ItemOldVersions
from .serializers import (DeleteItemSerializer, GetItemSerializer,
                          ItemStatisticSerializer, PutItemSerializer,
                          SalesItemSerializer)
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
            instance.price = avg_children_price(instance)
        print(instance.date)
        serializer = self.get_serializer(instance)
        self.get_all_children(serializer.data)
        print(serializer.data.get('date'))
        return Response(serializer.data)


class PutItemAPIView(generics.CreateAPIView, generics.UpdateAPIView):
    http_method_names = ['post']
    queryset = Item.objects.all()
    serializer_class = PutItemSerializer
    ## ощущение, что в тз хотят ограничение именно на количество иметов=1000
    ## а у меня количество запросов=1000, не разобрался пока как расширять
    ## throttle функционал
    throttle_scope = 'uploads'

    def create(self, request, *args, **kwargs):
        if (not request.data.get('items')) or not (
                request.data.get('updateDate')
        ):
            raise serializers.ValidationError

        for item in request.data['items']:
            if not validate_date(request.data['updateDate']):
                raise serializers.ValidationError
            item['date'] = validate_date(request.data['updateDate'])
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

        request_list = list(request.data['items'])
        step = 0
        while len(request_list) > 0:
            ## нашёл критическую ошибку в моём подходе:
            ## если хоть один item из списка будет невалиден,
            ## и он будет не первым в списке на создание,
            ## то у меня часть объектов создатся, а чать нет.
            ## прихожу к выводу, что нужно делать полную валидацию всех
            ## полей каждого объекта, перед тем как отправить их в цикл
            ## создания, но если я руками пишу валидацию, зачем мне вообще
            ## сериалайзеры...
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
                    self.perform_create(
                        serializer.save(parent=parent, date=item['date'])
                    )
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
    serializer_class = ItemStatisticSerializer
    throttle_scope = 'contacts'

    def get_queryset(self):
        if not self.kwargs.get('pk'):
            raise serializers.ValidationError
        if not uuid_validate(self.kwargs.get('pk')):
            raise serializers.ValidationError
        start_date = self.request.query_params.get('dateStart')
        end_date = self.request.query_params.get('dateEnd')
        if not start_date or not end_date:
            raise serializers.ValidationError
        start_date = validate_date(start_date)
        end_date = validate_date(end_date)
        if not start_date or not end_date or (start_date > end_date):
            raise serializers.ValidationError
        queryset = ItemOldVersions.objects.filter(
            actual_version=str(self.kwargs.get('pk')),
            date__range=(start_date, end_date),
        )
        if not queryset:
            raise Http404
        return queryset
