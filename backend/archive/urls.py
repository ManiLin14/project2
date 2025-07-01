"""
URL маршруты для API архива
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'websites', views.WebsiteViewSet, basename='website')
router.register(r'snapshots', views.ArchiveSnapshotViewSet, basename='snapshot')
router.register(r'pages', views.ArchivedPageViewSet, basename='page')

urlpatterns = [
    path('', include(router.urls)),
] 