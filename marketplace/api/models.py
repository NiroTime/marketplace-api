from datetime import datetime
import logging

from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from mptt.models import MPTTModel, TreeForeignKey


class Item(MPTTModel):
    id = models.UUIDField(primary_key=True, editable=True)
    name = models.CharField('Название', max_length=300)
    price = models.IntegerField('Цена', null=True, blank=True, default=None)
    date = models.DateTimeField()
    type = models.CharField(max_length=50)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        default=None, db_index=True, related_name='children'
    )

    def __str__(self):
        return self.name


class ItemOldVersions(models.Model):
    actual_version = models.CharField(max_length=36)
    name = models.CharField(max_length=300)
    price = models.IntegerField(null=True, blank=True, default=None)
    date = models.DateTimeField()
    type = models.CharField(max_length=50)
    parent = models.CharField(max_length=36)

    class Meta:
        ordering = ['-date']


def all_children_price_and_count(parent):
    """
    Функция принимает на вход родителя, считает сумарную стоимость
    и количество детей, возвращает среднюю стоимость или None, если
    у категории нет детей с типом OFFER.
    """
    try:
        children = parent.get_descendants()
    except Exception as err:
        logging.error(f'ошибка:{err}')
        children = None
    if children:
        all_offers_price = 0
        offers_count = 0
        for item in children:
            if item.type == 'OFFER':
                all_offers_price += item.price
                offers_count += 1
        try:
            return all_offers_price // offers_count
        except ZeroDivisionError:
            return None


@receiver(post_save, sender=Item)
def update_category_price(instance, **kwargs):
    """
    При изменении состояния ребёнка, функция вызывает изменение состояния
    родителя.
    """
    ## где-то страдает логика, при удаление эелементов не всегда работает
    try:
        ## первый трай нужен, когда мы удаляем категорию, но её дети вызывают
        ## instance.parent который уже удалён.
        if instance.parent:
            parent = instance.parent
            parent.price = all_children_price_and_count(parent)
            ## как различить делит и сейв сигналы?
            ## при делит сигнале нужно parent.date = datetime.now()
            ## из-за этого не архивируются изменеия при удалении
            parent.date = instance.date
            parent.save()
    except Exception as err:
        logging.error(
            f'Ошибка: {err}, в функции {update_category_price.__name__}'
        )


@receiver(post_delete, sender=Item)
def update_category_price(instance, **kwargs):
    signal_time = datetime.utcnow().replace(microsecond=0)
    print(signal_time)
    try:
        if instance.parent:
            parent = instance.parent
            parent.price = all_children_price_and_count(parent)
            parent.date = signal_time
            parent.save()
    except Exception as err:
        logging.error(
            f'Ошибка: {err}, в функции {update_category_price.__name__}'
        )


@receiver(post_save, sender=Item)
def create_item_old_version(instance, **kwargs):
    """
    Функция создаёт архинвую версию товара/категории, при создание/обновлении.
    """
    exist_old_version = ItemOldVersions.objects.filter(
        actual_version=str(instance.id)
    ).first()
    old_version = ItemOldVersions(
        actual_version=str(instance.id),
        name=instance.name,
        price=instance.price,
        date=instance.date,
        type=instance.type,
        parent=str(instance.parent),
    )
    ## ахитектурно выглядит плохо, но не могу придумать ничего лучше
    if exist_old_version:
        # страховка от дублирования архивных записей, в случае, если
        # в одном запросе этот объект изменяля многократно.
        if exist_old_version.date == instance.date:
            exist_old_version.price = instance.price
            exist_old_version.save()
            ## логика ломается, если в одном POST запросе придёт несколько
            ## обновлений одного товара, не понимаю нужно ли это архивировать
            ## как несколько изменений, или как одно
        else:
            old_version.save()
    else:
        old_version.save()


@receiver(post_delete, sender=Item)
def delete_all_old_version_on_item_delete(instance, **kwargs):
    """
    Функция удаляет архивные данные, если был удалён товар/категория.
    """
    old_versions = ItemOldVersions.objects.filter(
        actual_version=str(instance.id)
    )
    old_versions.delete()
