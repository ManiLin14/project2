from django.apps import AppConfig


class EncryptionConfig(AppConfig):
    """
    Конфигурация приложения шифрования
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'encryption'
    verbose_name = 'Шифрование AES 256' 