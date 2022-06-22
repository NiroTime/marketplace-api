from rest_framework import generics, ISO_8601
from rest_framework.fields import DateTimeField
from rest_framework.response import Response
from rest_framework.settings import api_settings

from .utils import avg_children_price_and_date


class ChangedListAPIView(generics.ListAPIView):

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        serializer_data = serializer.data
        return Response(data={"items": serializer_data})


class ChangedRetrieveAPIView(generics.RetrieveAPIView):

    def get_all_children(self, data, descendants_dict):
        """
        Рекурсивная функция распаковывающая детей
        у сериализованного объекта Item.
        """
        if data.get('children'):
            for step in range(len(data.get('children'))):
                item = descendants_dict[str(data.get('children')[step])]
                if item.type == 'CATEGORY':
                    item.price, item.date = avg_children_price_and_date(item)
                child = self.get_serializer(item).data
                data.get('children')[step] = child
                self.get_all_children(child, descendants_dict)
        elif data['type'] == 'OFFER':
            data['children'] = None


class MyDateTimeField(DateTimeField):
    def to_representation(self, value):
        if not value:
            return None

        output_format = getattr(self, 'format', api_settings.DATETIME_FORMAT)

        if output_format is None or isinstance(value, str):
            return value

        value = self.enforce_timezone(value)

        if output_format.lower() == ISO_8601:
            value = value.isoformat(sep='T', timespec='milliseconds')
            if value.endswith('+00:00'):
                value = value[:-6] + 'Z'
            return value
        return value.strftime(output_format)
