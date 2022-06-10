from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Item, ItemArchiveVersions
from .utils import avg_children_price


@receiver(post_save, sender=Item)
def create_item_archive_version(instance, **kwargs):
    """
    Функция создаёт архинвую версию товара/категории, при создание/обновлении.
    """
    exist_archive_version = ItemArchiveVersions.objects.filter(
        actual_version=str(instance.pk)
    ).first()
    fresh_archive_version = ItemArchiveVersions(
        actual_version=str(instance.id),
        name=instance.name,
        price=instance.price,
        date=instance.date,
        type=instance.type,
        parent=str(instance.parent),
    )
    if instance.type == 'CATEGORY':
        fresh_archive_version.price, date = avg_children_price(
            instance
        )
        if fresh_archive_version.date < date:
            fresh_archive_version.date = date
        if exist_archive_version:
            if exist_archive_version.date == fresh_archive_version.date:
                exist_archive_version.price = fresh_archive_version.price
                exist_archive_version.save()
            else:
                fresh_archive_version.save()
        else:
            fresh_archive_version.save()
    else:
        fresh_archive_version.save()


@receiver(post_delete, sender=Item)
def delete_all_old_version_on_item_delete(instance, **kwargs):
    """
    Функция удаляет архивные данные, если был удалён товар/категория.
    """
    old_versions = ItemArchiveVersions.objects.filter(
        actual_version=str(instance.id)
    )
    old_versions.delete()
