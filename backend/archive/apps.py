from django.apps import AppConfig


class ArchiveConfig(AppConfig):
    """
    Конфигурация приложения архивирования
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'archive'
    verbose_name = 'Веб-архив' 