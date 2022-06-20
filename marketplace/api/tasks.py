from celery import shared_task

from .models import Item, ItemArchiveVersions
from .utils import create_item_archive_version


@shared_task
def save_archive_versions(items_id_set):
    archive_items_list = []
    items = Item.objects.filter(pk__in=items_id_set)
    items_for_archiving = items.get_ancestors(include_self=True)
    for item in set(items_for_archiving):
        archive_items_list.append(
            create_item_archive_version(instance=item)
        )
    ItemArchiveVersions.objects.bulk_create(archive_items_list)
