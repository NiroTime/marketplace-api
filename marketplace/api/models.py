from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Item(MPTTModel):
    id = models.UUIDField(primary_key=True, editable=True)
    name = models.CharField(max_length=300)
    price = models.IntegerField(null=True, blank=True, default=None)
    date = models.DateTimeField()
    type = models.CharField(max_length=50)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        default=None, db_index=True, related_name='children'
    )

    def __str__(self):
        return str(self.pk)


class ItemArchiveVersions(models.Model):
    actual_version = models.CharField(max_length=36)
    name = models.CharField(max_length=300)
    price = models.IntegerField(null=True, blank=True, default=None)
    date = models.DateTimeField()
    type = models.CharField(max_length=50)
    parent = models.CharField(max_length=36)

    class Meta:
        ordering = ['-date']
