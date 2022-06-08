from datetime import datetime, timedelta

from django.http import Http404
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .models import Item, ItemOldVersions, avg_children_price
from .utils import ChangedListAPIView, uuid_validate, ItemNotInDBError
from .serializers import (DeleteItemSerializer, GetItemSerializer,
                          ItemStatisticSerializer, PutItemSerializer,
                          SalesItemSerializer)


class GetItemAPIView(generics.RetrieveAPIView):
    http_method_names = ['get']
    queryset = Item.objects.all()
    serializer_class = GetItemSerializer
    throttle_scope = 'contacts'

    ## можно переопределить RetrieveAPIView в utils вместе с этим методом,
    ## чтобы сократить количество кода в views но в плане наглядности,
    ## не уверен что это норм
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
                if item.type == 'CATEGORY':
                    item.price = avg_children_price(item)
                child = self.get_serializer(item).data
                data.get('children')[step] = child
                self.get_all_children(child)
                step += 1

    def retrieve(self, request, *args, **kwargs):
        if not uuid_validate(kwargs.get('pk')):
            raise serializers.ValidationError
        instance = self.get_object()
        if instance.type == 'CATEGORY':
            instance.price = avg_children_price(instance)
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
        temp_data = []
        request_list = list(request.data['items'])
        step = 0
        while len(request_list) > 0:
            try:
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
                    if not item.get('parent'):
                        parent = None
                    else:
                        parent = Item.objects.get(pk=item.get('parent'))
                    self.perform_create(serializer.save(parent=parent))
                    temp_data.append(Item(
                        id=serializer.validated_data.get('id'),
                        name=serializer.validated_data.get('name'),
                        price=serializer.validated_data.get('price'),
                        date=serializer.validated_data.get('date'),
                        type=serializer.validated_data.get('type'),
                        parent=parent,
                    ))
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
        ## но он не умеет понимать когда сохранять, а когда создавать(

        # for item in temp_data:
        #     item.save()
        print(temp_data)
        ## если вот тут вызывать функцию, которая будет перерасчитывать
        ## цену категории, то это может сильно сократить нагрузу на БД
        ## т.к сигналы вызваются при добавлении каждого объекта.

        ## Как мне без сигналов понять: цены каких категорий стоит обновлять,
        ## неужели придётся после каждого запроса полностью проходиться по
        ## всей базе

        ## я ещё не понимаю как всё это под капотом работает, но много вопросов
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
        self.perform_destroy(instance)
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
