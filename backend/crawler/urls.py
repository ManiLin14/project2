"""
URL маршруты для API краулера
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('start-crawl/', views.start_crawl, name='start_crawl'),
    path('crawl-status/<str:task_id>/', views.crawl_status, name='crawl_status'),
] 