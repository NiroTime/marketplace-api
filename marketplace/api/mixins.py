from rest_framework import generics
from rest_framework.response import Response

from .utils import avg_children_price_and_date, validate_date


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

    def get_all_children(self, data, descendants_dict):
        """
        Рекурсивная функция распаковывающая детей
        у сериализованного объекта Item.
        """
        if data.get('children'):
            step = 0
            while step < len(data.get('children')):
                item = descendants_dict[str(data.get('children')[step])]
                if item.type == 'CATEGORY':
                    item.price, item.date = avg_children_price_and_date(item)
                child = self.get_serializer(item).data
                child['date'] = validate_date(
                    child['date']
                ).isoformat(sep='T', timespec='milliseconds') + 'Z'
                data.get('children')[step] = child
                self.get_all_children(child, descendants_dict)
                step += 1
        elif data['type'] == 'OFFER':
            data['children'] = None

