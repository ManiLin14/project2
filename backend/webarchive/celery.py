"""
Celery configuration для веб-архива.
"""
import os
from celery import Celery

# Устанавливаем настройки Django для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webarchive.settings')

app = Celery('webarchive')

# Используем строку здесь, чтобы worker не нужно было сериализовать
# объект конфигурации для дочерних процессов.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Загружаем модули задач из всех зарегистрированных Django приложений.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 