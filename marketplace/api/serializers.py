from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import Item, ItemOldVersions


class GetItemSerializer(serializers.ModelSerializer):
    parentId = serializers.UUIDField(source='parent')

    class Meta:
        model = Item
        fields = (
            'name', 'type', 'id', 'parentId', 'date', 'price', 'children',
        )


class PutItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = ('id', 'name', 'type', 'parent', 'date', 'price',)

    def validate(self, data):
        # Проверяем валидность типа товара
        if data['type'] not in ('OFFER', 'CATEGORY'):
            raise serializers.ValidationError
        if (data['type'] == 'CATEGORY') and (data.get('price')):
            raise serializers.ValidationError
        if (data['type'] == 'OFFER') and not (data.get('price')):
            raise serializers.ValidationError

        # Проверяем валидность переданного parentId
        if data.get('parentId'):
            parent_item = get_object_or_404(Item, pk=data['id'])
            if parent_item.type != 'CATEGORY':
                raise serializers.ValidationError

        # Нельзя менять тип с OFFER на CATEGORY и наоборот
        current_item = Item.objects.filter(pk=data['id']).first()
        if current_item:
            if current_item.type != data['type']:
                raise serializers.ValidationError
        return data


class DeleteItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item


class SalesItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = ('id', 'name', 'type', 'parent', 'date', 'price',)


class ItemStatisticSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='actual_version')

    class Meta:
        model = ItemOldVersions
        fields = ('id', 'name', 'type', 'parent', 'date', 'price',)
