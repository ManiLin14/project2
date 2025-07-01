"""
Модели для веб-архива
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from encryption.aes_cipher import AESCipher
import uuid


class Website(models.Model):
    """
    Модель для отслеживаемых веб-сайтов
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=2048, verbose_name="URL сайта")
    domain = models.CharField(max_length=255, verbose_name="Домен")
    title = models.CharField(max_length=500, blank=True, verbose_name="Заголовок")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создано пользователем")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    crawl_depth = models.IntegerField(default=3, verbose_name="Глубина сканирования")
    
    class Meta:
        verbose_name = "Веб-сайт"
        verbose_name_plural = "Веб-сайты"
        unique_together = ['url', 'created_by']
        
    def __str__(self):
        return f"{self.domain} - {self.title}"


class ArchiveSnapshot(models.Model):
    """
    Снапшот архива сайта
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='snapshots')
    snapshot_date = models.DateTimeField(default=timezone.now, verbose_name="Дата снапшота")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Ожидает'),
            ('processing', 'Обработка'),
            ('completed', 'Завершен'),
            ('failed', 'Ошибка'),
        ],
        default='pending',
        verbose_name="Статус"
    )
    pages_count = models.IntegerField(default=0, verbose_name="Количество страниц")
    assets_count = models.IntegerField(default=0, verbose_name="Количество ресурсов")
    total_size = models.BigIntegerField(default=0, verbose_name="Общий размер (байты)")
    
    # Зашифрованные метаданные
    _encrypted_metadata = models.TextField(blank=True, verbose_name="Метаданные")
    
    class Meta:
        verbose_name = "Снапшот архива"
        verbose_name_plural = "Снапшоты архивов"
        ordering = ['-snapshot_date']
        
    def __str__(self):
        return f"{self.website.domain} - {self.snapshot_date.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def metadata(self):
        """
        Получить расшифрованные метаданные
        """
        if self._encrypted_metadata:
            cipher = AESCipher()
            return cipher.decrypt(self._encrypted_metadata)
        return {}
    
    @metadata.setter
    def metadata(self, value):
        """
        Установить зашифрованные метаданные
        """
        if value:
            cipher = AESCipher()
            self._encrypted_metadata = cipher.encrypt(str(value))


class ArchivedPage(models.Model):
    """
    Архивированная веб-страница
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(ArchiveSnapshot, on_delete=models.CASCADE, related_name='pages')
    url = models.URLField(max_length=2048, verbose_name="URL страницы")
    title = models.CharField(max_length=500, blank=True, verbose_name="Заголовок")
    status_code = models.IntegerField(default=200, verbose_name="HTTP статус")
    content_type = models.CharField(max_length=100, default='text/html', verbose_name="MIME тип")
    archived_at = models.DateTimeField(default=timezone.now, verbose_name="Дата архивирования")
    
    # Зашифрованный контент
    _encrypted_content = models.TextField(verbose_name="Зашифрованный контент")
    
    # Размер и хеш
    content_size = models.IntegerField(default=0, verbose_name="Размер контента")
    content_hash = models.CharField(max_length=64, verbose_name="Хеш контента")
    
    # Скриншот
    screenshot_path = models.CharField(max_length=500, blank=True, verbose_name="Путь к скриншоту")
    
    class Meta:
        verbose_name = "Архивированная страница"
        verbose_name_plural = "Архивированные страницы"
        unique_together = ['snapshot', 'url']
        
    def __str__(self):
        return f"{self.title} - {self.url}"
    
    @property
    def content(self):
        """
        Получить расшифрованный контент
        """
        if self._encrypted_content:
            cipher = AESCipher()
            return cipher.decrypt(self._encrypted_content)
        return ""
    
    @content.setter
    def content(self, value):
        """
        Установить зашифрованный контент
        """
        if value:
            cipher = AESCipher()
            self._encrypted_content = cipher.encrypt(value)


class ArchivedAsset(models.Model):
    """
    Архивированный ресурс (CSS, JS, изображения)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(ArchiveSnapshot, on_delete=models.CASCADE, related_name='assets')
    url = models.URLField(max_length=2048, verbose_name="URL ресурса")
    asset_type = models.CharField(
        max_length=20,
        choices=[
            ('css', 'CSS'),
            ('js', 'JavaScript'),
            ('image', 'Изображение'),
            ('font', 'Шрифт'),
            ('other', 'Другое'),
        ],
        default='other',
        verbose_name="Тип ресурса"
    )
    file_path = models.CharField(max_length=500, verbose_name="Путь к файлу")
    file_size = models.BigIntegerField(default=0, verbose_name="Размер файла")
    content_type = models.CharField(max_length=100, blank=True, verbose_name="MIME тип")
    archived_at = models.DateTimeField(default=timezone.now, verbose_name="Дата архивирования")
    
    class Meta:
        verbose_name = "Архивированный ресурс"
        verbose_name_plural = "Архивированные ресурсы"
        unique_together = ['snapshot', 'url']
        
    def __str__(self):
        return f"{self.asset_type} - {self.url}" 