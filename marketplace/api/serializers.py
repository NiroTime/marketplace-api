from rest_framework import serializers

from .mixins import MyDateTimeField
from .models import Item, ItemArchiveVersions


class GetItemSerializer(serializers.ModelSerializer):
    parentId = serializers.UUIDField(source='parent')
    date = MyDateTimeField()

    class Meta:
        model = Item
        fields = (
            'name', 'type', 'id', 'parentId', 'date', 'price', 'children',
        )


class PutItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = ('id', 'name', 'date', 'type', 'price',)

    def validate(self, data):
        # Проверяем валидность типа товара
        if data['type'] not in ('OFFER', 'CATEGORY'):
            raise serializers.ValidationError
        if (data['type'] == 'CATEGORY') and (data.get('price')):
            raise serializers.ValidationError
        if (data['type'] == 'OFFER') and (not data.get('price') or int(
                data.get('price')) < 0):
            raise serializers.ValidationError

        # Нельзя менять тип с OFFER на CATEGORY и наоборот
        current_item = Item.objects.filter(pk=data['id']).first()
        if current_item and current_item.type != data['type']:
            raise serializers.ValidationError
        return data


class DeleteItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item


class SalesItemSerializer(serializers.ModelSerializer):
    date = MyDateTimeField()

    class Meta:
        model = Item
        fields = ('id', 'name', 'type', 'parent', 'date', 'price',)


class ItemStatisticSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='actual_version')
    date = MyDateTimeField()

    class Meta:
        model = ItemArchiveVersions
        fields = ('id', 'name', 'type', 'parent', 'date', 'price',)
