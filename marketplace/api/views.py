from datetime import datetime, timedelta

from django.http import Http404
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .models import Item, ItemOldVersions
from .utils import (avg_children_price, ChangedListAPIView,
                    uuid_validate, ItemNotInDBError, ChangedRetrieveAPIView,)
from .serializers import (DeleteItemSerializer, GetItemSerializer,
                          ItemStatisticSerializer, PutItemSerializer,
                          SalesItemSerializer,)


class GetItemAPIView(ChangedRetrieveAPIView):
    http_method_names = ['get']
    queryset = Item.objects.all()
    serializer_class = GetItemSerializer
    throttle_scope = 'contacts'

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
            item['date'] = request.data['updateDate']
            # Удаляем атрибут price из входных данных если он не определён
            if 'price' in item.keys():
                price = item.get('price')
                if (not price) or (price == "None") or (price == "Null"):
                    item.pop('price')
            # Добавляем ключ parent если он определён
            if 'parentId' in item.keys():
                parent = item.get('parentId')
                ## пояснение: в дальнейшем мы будем пользоваться только parent
                ## поэтому ключ parentId мы не удаляем
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

        ## по условию задачи итемы идут неупорядачено, то есть мне нельзя
        ## создавать их по очереди, нужно создавать только если нет родителя
        ## или он уже в базе
        request_list = list(request.data['items'])
        temp_data = []
        step = 0
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
                    self.perform_create(serializer.save(parent=parent))
                    temp_data.append(serializer.validated_data.get('id'))
                    request_list.remove(item)
                    step = 0
                    if method == 'PUT':
                        if getattr(
                                instance, '_prefetched_objects_cache', None
                        ):
                            instance._prefetched_objects_cache = {}
                except Exception as err:
                    print(err)
                    raise ItemNotInDBError
            except ItemNotInDBError:
                step += 1
        ## очень хочется показать, что я знаю, что такое bulk_create,
        ## но он не умеет понимать когда сохранять, а когда создавать
        ancestors = []
        for item_id in temp_data:
            item = Item.objects.get(pk=item_id)
            if item.parent:
                ancestors += item.get_ancestors()
        print('\n', set(ancestors))
        for item in ancestors:
            item.price = avg_children_price(item)
            item.date = request.data['updateDate']
            item.save()

        ## я не понимаю как всё это под капотом работает, но много вопросов
        ## кажется лучше обновлять цены категорий уже после отправки ответа
        ## клиенту, но не знаю как это сделать, с другой стороны, будет ли
        ## доступен сервис в то время, пока обновляются цены категорий?
        return Response(status=HTTP_200_OK)


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
        print('\n', ancestors)
        for item in ancestors:
            item.price = avg_children_price(item)
            item.date = datetime.utcnow().replace(microsecond=0)
            item.save()
        return Response(status=HTTP_200_OK)


class SalesItemAPIView(ChangedListAPIView):
    serializer_class = SalesItemSerializer
    throttle_scope = 'contacts'

    def get_queryset(self):
        end_date = self.request.query_params.get('date')
        if not end_date:
            raise serializers.ValidationError
        ## думал воспользоваться dateutil, но не до конца понимаю, стоит ли
        ## пытаться обработать запросы кроме этих 2х форматов?
        ## если не пользоваться dateutil, стоит ли вынести эти 2 блока try
        ## как функцию в utils?
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
