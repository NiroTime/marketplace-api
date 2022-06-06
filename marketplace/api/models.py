import uuid

from django.db import models
from django.db.models.signals import post_save, post_delete
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

    @receiver(post_save)
    def update_category_price(sender, instance, **kwargs):
        if instance.price and instance.parent:
            parent = Item.objects.filter(pk=instance.parent.id).first()
            if parent:
                new_price = 0
                children_count = len(parent.get_children())
                for item in parent.get_children():
                    if item.price:
                        new_price += item.price
                parent.price = new_price // children_count
                parent.save()


