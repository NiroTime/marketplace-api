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


## Ощущение, что хранить сигналы стоит в отдельно файле, пробовал создать
## signals.py но почему то там сигналы не приходили, при таком же синтаксисе

## От сигналов точно нужно избавляться, и переносить логику обновления
## категори в конец вьюхи пост запроса, даже при 20 итемах в базе, ответ
## постмана уже 500мс
# @receiver(post_save, sender=Item)
# def update_parent_category_price_on_save(instance, **kwargs):
#     """
#     При изменении состояния ребёнка, функция вызывает изменение состояния
#     родителя.
#     """
#     ## где-то страдает логика, при удаление эелементов не всегда работает
#     try:
#         ## первый трай нужен, когда мы удаляем категорию, но её дети вызывают
#         ## instance.parent который уже удалён.
#         if instance.parent:
#             parent = instance.parent
#             parent.price = avg_children_price(parent)
#             ## как различить делит и сейв сигналы?
#             ## при делит сигнале нужно parent.date = datetime.now()
#             ## из-за этого не архивируются изменеия при удалении
#             parent.date = instance.date
#             parent.save()
#     except Exception as err:
#         logging.error(
#             f'Ошибка: {err}, в функции '
#             f'{update_parent_category_price_on_save.__name__}'
#         )
#
#
# @receiver(post_delete, sender=Item)
# def update_parent_category_price_on_delete(instance, **kwargs):
#     signal_time = datetime.utcnow().replace(microsecond=0)
#     try:
#         if instance.parent:
#             parent = instance.parent
#             parent.price = avg_children_price(parent)
#             parent.date = signal_time
#             parent.save()
#     except Exception as err:
#         logging.error(
#             f'Ошибка: {err}, в функции '
#             f'{update_parent_category_price_on_delete.__name__}'
#         )


@receiver(post_save, sender=Item)
def create_item_old_version(instance, **kwargs):
    """
    Функция создаёт архинвую версию товара/категории, при создание/обновлении.
    """
    exist_old_version = ItemOldVersions.objects.filter(
        actual_version=str(instance.id)
    ).first()
    print(exist_old_version)
    new_version = ItemOldVersions(
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
            print('\n', exist_old_version, exist_old_version.date, 'refresh')
            exist_old_version.save()
            ## логика ломается, если в одном POST запросе придёт несколько
            ## обновлений одного товара, не понимаю нужно ли это архивировать
            ## как несколько изменений, или как одно, и является ли такой
            ## запрос валидным
        else:
            print('\n', new_version, new_version.date, exist_old_version.date, 'create')
            new_version.save()
    else:
        print('\n', new_version, new_version.date, 'create')
        new_version.save()


@receiver(post_delete, sender=Item)
def delete_all_old_version_on_item_delete(instance, **kwargs):
    """
    Функция удаляет архивные данные, если был удалён товар/категория.
    """
    old_versions = ItemOldVersions.objects.filter(
        actual_version=str(instance.id)
    )
    old_versions.delete()
