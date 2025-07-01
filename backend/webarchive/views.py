"""
Представления для главной страницы веб-архива
"""
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.conf import settings
import os


def home_view(request):
    """Главная страница веб-архива"""
    # Путь к фронтенд файлам
    frontend_path = os.path.join(settings.BASE_DIR.parent, 'frontend')
    
    # Читаем HTML файл
    try:
        with open(os.path.join(frontend_path, 'index.html'), 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HttpResponse(html_content)
    except FileNotFoundError:
        return HttpResponse('<h1>Фронтенд не найден</h1>')


def frontend_static(request, filename):
    """Отдача статических файлов фронтенда"""
    frontend_path = os.path.join(settings.BASE_DIR.parent, 'frontend')
    file_path = os.path.join(frontend_path, filename)
    
    if not os.path.exists(file_path):
        return HttpResponse('Файл не найден', status=404)
    
    # Определяем content-type
    content_type = 'text/plain'
    if filename.endswith('.css'):
        content_type = 'text/css'
    elif filename.endswith('.js'):
        content_type = 'application/javascript'
    elif filename.endswith('.html'):
        content_type = 'text/html'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type=content_type)
    except Exception as e:
        return HttpResponse(f'Ошибка чтения файла: {str(e)}', status=500) 