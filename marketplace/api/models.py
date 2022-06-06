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

    def __str__(self):
        return self.name


class RecursionHelper:
    def __init__(self, new_price, current_offers_count):
        self.all_offers_price = new_price
        self.offers_count = current_offers_count

    def refresh(self):
        self.all_offers_price = 0
        self.offers_count = 0


average_price = RecursionHelper(0, 0)


def all_children_price_and_count(parent):
    """
    Функция принимает на вход родителя, и с помощью
    вспомогательного объекта average_price, считает сумарную стоимость
    и количество детей.
    """
    children = parent.get_children()
    if children:
        step = 0
        while step < len(children):
            if children[step].type == 'OFFER':
                average_price.all_offers_price += children[step].price
                average_price.offers_count += 1
            else:
                all_children_price_and_count(children[step])
            step += 1
    else:
        return None


@receiver(post_delete, sender=Item)
@receiver(post_save, sender=Item)
def update_category_price(instance, **kwargs):
    """
    При изменении состояния ребёнка, функция вызывает изменение состояния
    родителя.
    """
    try:
        if instance.parent:
            parent = instance.parent
            all_children_price_and_count(parent)
            parent.price = (
                    average_price.all_offers_price //
                    average_price.offers_count
            )
            average_price.refresh()
            parent.save()
    except Exception as err:
        logging.error(
            f'Ошибка: {err}, в функции {update_category_price.__name__}'
        )
