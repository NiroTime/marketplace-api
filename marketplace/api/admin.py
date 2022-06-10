from django.contrib import admin

from .models import Item, ItemArchiveVersions


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


@admin.register(ItemArchiveVersions)
class ItemOldVersionAdmin(admin.ModelAdmin):
    list_display = (
        'actual_version',
        'name',
        'price',
        'date',
        'type',
        'parent',
    )
