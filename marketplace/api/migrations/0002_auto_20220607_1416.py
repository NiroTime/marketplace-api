# Generated by Django 2.2.19 on 2022-06-07 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itemoldversions',
            options={'ordering': ['-date']},
        ),
        migrations.AlterField(
            model_name='item',
            name='id',
            field=models.UUIDField(primary_key=True, serialize=False),
        ),
    ]