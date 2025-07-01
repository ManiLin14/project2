# Generated manually
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Website',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('url', models.URLField(max_length=2048, verbose_name='URL сайта')),
                ('domain', models.CharField(max_length=255, verbose_name='Домен')),
                ('title', models.CharField(blank=True, max_length=500, verbose_name='Заголовок')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('crawl_depth', models.IntegerField(default=3, verbose_name='Глубина сканирования')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Создано пользователем')),
            ],
            options={
                'verbose_name': 'Веб-сайт',
                'verbose_name_plural': 'Веб-сайты',
            },
        ),
        migrations.CreateModel(
            name='ArchiveSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('snapshot_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата снапшота')),
                ('status', models.CharField(choices=[('pending', 'Ожидает'), ('processing', 'Обработка'), ('completed', 'Завершен'), ('failed', 'Ошибка')], default='pending', max_length=20, verbose_name='Статус')),
                ('pages_count', models.IntegerField(default=0, verbose_name='Количество страниц')),
                ('assets_count', models.IntegerField(default=0, verbose_name='Количество ресурсов')),
                ('total_size', models.BigIntegerField(default=0, verbose_name='Общий размер (байты)')),
                ('_encrypted_metadata', models.TextField(blank=True, verbose_name='Метаданные')),
                ('website', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='snapshots', to='archive.website')),
            ],
            options={
                'verbose_name': 'Снапшот архива',
                'verbose_name_plural': 'Снапшоты архивов',
                'ordering': ['-snapshot_date'],
            },
        ),
        migrations.CreateModel(
            name='ArchivedPage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('url', models.URLField(max_length=2048, verbose_name='URL страницы')),
                ('title', models.CharField(blank=True, max_length=500, verbose_name='Заголовок')),
                ('archived_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата архивирования')),
                ('_encrypted_content', models.TextField(verbose_name='Зашифрованный контент')),
                ('content_size', models.IntegerField(default=0, verbose_name='Размер контента')),
                ('content_hash', models.CharField(max_length=64, verbose_name='Хеш контента')),
                ('screenshot_path', models.CharField(blank=True, max_length=500, verbose_name='Путь к скриншоту')),
                ('snapshot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='archive.archivesnapshot')),
            ],
            options={
                'verbose_name': 'Архивированная страница',
                'verbose_name_plural': 'Архивированные страницы',
            },
        ),
        migrations.CreateModel(
            name='ArchivedAsset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('url', models.URLField(max_length=2048, verbose_name='URL ресурса')),
                ('asset_type', models.CharField(choices=[('css', 'CSS'), ('js', 'JavaScript'), ('image', 'Изображение'), ('font', 'Шрифт'), ('other', 'Другое')], default='other', max_length=20, verbose_name='Тип ресурса')),
                ('file_path', models.CharField(max_length=500, verbose_name='Путь к файлу')),
                ('file_size', models.BigIntegerField(default=0, verbose_name='Размер файла')),
                ('content_type', models.CharField(blank=True, max_length=100, verbose_name='MIME тип')),
                ('archived_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата архивирования')),
                ('snapshot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='archive.archivesnapshot')),
            ],
            options={
                'verbose_name': 'Архивированный ресурс',
                'verbose_name_plural': 'Архивированные ресурсы',
            },
        ),
        migrations.AlterUniqueTogether(
            name='website',
            unique_together={('url', 'created_by')},
        ),
        migrations.AlterUniqueTogether(
            name='archivedpage',
            unique_together={('snapshot', 'url')},
        ),
        migrations.AlterUniqueTogether(
            name='archivedasset',
            unique_together={('snapshot', 'url')},
        ),
    ] 