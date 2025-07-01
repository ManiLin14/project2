"""webarchive URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),  # Главная страница
    path('admin/', admin.site.urls),
    path('api/v1/archive/', include('archive.urls')),
        path('api/v1/crawler/', include('crawler.urls')),
    
    # Статические файлы фронтенда
    path('styles.css', views.frontend_static, {'filename': 'styles.css'}, name='frontend_css'),
    path('main.js', views.frontend_static, {'filename': 'main.js'}, name='frontend_js'),
]

# Статические файлы в development режиме
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 