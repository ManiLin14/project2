from django.apps import AppConfig


class CrawlerConfig(AppConfig):
    """
    Конфигурация приложения краулера
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crawler'
    verbose_name = 'Веб-краулер' 