"""
API views для веб-архива
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from .models import Website, ArchiveSnapshot, ArchivedPage
from .serializers import (
    WebsiteSerializer, ArchiveSnapshotSerializer,
    ArchiveSnapshotListSerializer, ArchivedPageSerializer
)
from encryption.file_encryption import ArchiveFileEncryption
import logging

logger = logging.getLogger(__name__)


class WebsiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления веб-сайтами
    """
    serializer_class = WebsiteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Получаем только сайты текущего пользователя"""
        return Website.objects.filter(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def snapshots(self, request, pk=None):
        """
        Получение списка снапшотов для сайта
        
        GET /api/v1/archive/websites/{id}/snapshots/
        """
        website = self.get_object()
        snapshots = website.snapshots.all()
        serializer = ArchiveSnapshotListSerializer(snapshots, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def latest_snapshot(self, request, pk=None):
        """
        Получение последнего снапшота
        
        GET /api/v1/archive/websites/{id}/latest_snapshot/
        """
        website = self.get_object()
        latest = website.snapshots.first()
        
        if not latest:
            return Response(
                {'message': 'Снапшоты не найдены'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ArchiveSnapshotSerializer(latest)
        return Response(serializer.data)


class ArchiveSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра снапшотов архивов
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Получаем только снапшоты сайтов текущего пользователя"""
        return ArchiveSnapshot.objects.filter(
            website__created_by=self.request.user
        )
    
    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия"""
        if self.action == 'list':
            return ArchiveSnapshotListSerializer
        return ArchiveSnapshotSerializer
    
    @action(detail=True, methods=['get'])
    def pages(self, request, pk=None):
        """
        Получение страниц снапшота
        
        GET /api/v1/archive/snapshots/{id}/pages/
        """
        snapshot = self.get_object()
        pages = snapshot.pages.all()
        serializer = ArchivedPageSerializer(pages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def page_content(self, request, pk=None):
        """
        Получение контента конкретной страницы
        
        GET /api/v1/archive/snapshots/{id}/page_content/?url=<page_url>
        """
        snapshot = self.get_object()
        page_url = request.query_params.get('url')
        
        if not page_url:
            return Response(
                {'error': 'Параметр url обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            page = snapshot.pages.get(url=page_url)
            
            # Получаем расшифрованный контент
            content = page.content
            
            return HttpResponse(
                content,
                content_type='text/html; charset=utf-8'
            )
            
        except ArchivedPage.DoesNotExist:
            return Response(
                {'error': 'Страница не найдена в архиве'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """
        Получение снапшотов по дате (календарный просмотр)
        
        GET /api/v1/archive/snapshots/by_date/?year=2024&month=1&day=15
        """
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        day = request.query_params.get('day')
        
        queryset = self.get_queryset()
        
        if year:
            queryset = queryset.filter(snapshot_date__year=year)
        if month:
            queryset = queryset.filter(snapshot_date__month=month)
        if day:
            queryset = queryset.filter(snapshot_date__day=day)
        
        serializer = ArchiveSnapshotListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Поиск по архивам
        
        GET /api/v1/archive/snapshots/search/?q=search_term&domain=example.com
        """
        query = request.query_params.get('q', '')
        domain = request.query_params.get('domain', '')
        
        queryset = self.get_queryset()
        
        if domain:
            queryset = queryset.filter(website__domain__icontains=domain)
        
        if query:
            queryset = queryset.filter(
                website__title__icontains=query
            ) | queryset.filter(
                website__description__icontains=query
            )
        
        serializer = ArchiveSnapshotListSerializer(queryset, many=True)
        return Response(serializer.data)


class ArchivedPageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра архивированных страниц
    """
    serializer_class = ArchivedPageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Получаем только страницы архивов текущего пользователя"""
        return ArchivedPage.objects.filter(
            snapshot__website__created_by=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        """
        Получение полного контента страницы
        
        GET /api/v1/archive/pages/{id}/content/
        """
        page = self.get_object()
        
        # Получаем расшифрованный контент
        content = page.content
        
        return HttpResponse(
            content,
            content_type='text/html; charset=utf-8'
        ) 