from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'price',
        'date',
        'type',
        'parent',
    )
