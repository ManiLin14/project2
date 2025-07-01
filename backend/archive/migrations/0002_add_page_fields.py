# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='archivedpage',
            name='status_code',
            field=models.IntegerField(default=200, verbose_name='HTTP статус'),
        ),
        migrations.AddField(
            model_name='archivedpage',
            name='content_type',
            field=models.CharField(default='text/html', max_length=100, verbose_name='MIME тип'),
        ),
    ] 