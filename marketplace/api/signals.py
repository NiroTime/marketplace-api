from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Item, ItemArchiveVersions


@receiver(post_delete, sender=Item)
def delete_all_old_version_on_item_delete(instance, **kwargs):
    """
    Функция удаляет архивные данные, если был удалён товар/категория.
    """
    old_versions = ItemArchiveVersions.objects.filter(
        actual_version=str(instance.id)
    )
    old_versions.delete()
