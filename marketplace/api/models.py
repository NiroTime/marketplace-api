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
        return str(self.pk)


class ItemOldVersions(models.Model):
    actual_version = models.CharField(max_length=36)
    name = models.CharField(max_length=300)
    price = models.IntegerField(null=True, blank=True, default=None)
    date = models.DateTimeField()
    type = models.CharField(max_length=50)
    parent = models.CharField(max_length=36)

    class Meta:
        ordering = ['-date']


@receiver(post_save, sender=Item)
def create_item_old_version(instance, **kwargs):
    """
    Функция создаёт архинвую версию товара/категории, при создание/обновлении.
    """
    ItemOldVersions(
        actual_version=str(instance.id),
        name=instance.name,
        price=instance.price,
        date=instance.date,
        type=instance.type,
        parent=str(instance.parent),
    ).save()
    ## почему сигнал вызывается 2 раза?


@receiver(post_delete, sender=Item)
def delete_all_old_version_on_item_delete(instance, **kwargs):
    """
    Функция удаляет архивные данные, если был удалён товар/категория.
    """
    old_versions = ItemOldVersions.objects.filter(
        actual_version=str(instance.id)
    )
    old_versions.delete()
