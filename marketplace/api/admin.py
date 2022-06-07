from django.contrib import admin

from .models import Item, ItemOldVersions


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


@admin.register(ItemOldVersions)
class ItemOldVersionAdmin(admin.ModelAdmin):
    list_display = (
        'actual_version',
        'name',
        'price',
        'date',
        'type',
        'parent',
    )
