import logging
import uuid

from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from mptt.models import MPTTModel, TreeForeignKey


class Item(MPTTModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    name = models.CharField('Название', max_length=300)
    price = models.IntegerField('Цена', null=True, blank=True, default=None)
    date = models.DateTimeField()
    type = models.CharField(max_length=20)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        default=None, db_index=True, related_name='children'
    )


def update_category_price(instance):
    """Функция изменяет состояние родителя, если изменилось состояние сына."""
    try:
        if instance.parent:
            parent = Item.objects.filter(pk=instance.parent.id).first()
            if parent:
                if parent.get_children():
                    new_price = 0
                    children_count = 0
                    for item in parent.get_children():
                        if item.price:
                            children_count += 1
                            new_price += item.price
                    try:
                        parent.price = new_price // children_count
                    except ZeroDivisionError:
                        parent.price = None
                    parent.save()
                else:
                    parent.price = None
                    parent.save()
    except Exception as err:
        print(err)
        logging.error(f'{instance} ошибка: {err}')


@receiver(post_save, sender=Item)
def update_price_on_save(instance, **kwargs):
    update_category_price(instance=instance)


@receiver(post_delete, sender=Item)
def update_price_on_delete(instance, **kwargs):
    update_category_price(instance=instance)
