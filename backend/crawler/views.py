"""
API views для веб-краулера
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from celery.result import AsyncResult
from archive.models import Website
from archive.serializers import CreateSnapshotSerializer
from .tasks import crawl_website_task
import logging

logger = logging.getLogger(__name__)


class StartCrawlView(APIView):
    """
    API для запуска сканирования веб-сайта
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Запуск сканирования веб-сайта
        
        POST /api/v1/crawler/start/
        {
            "website_id": "uuid",
            "crawl_depth": 3,
            "follow_external_links": false
        }
        """
        serializer = CreateSnapshotSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Неверные данные', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            website_id = serializer.validated_data['website_id']
            crawl_depth = serializer.validated_data.get('crawl_depth', 3)
            follow_external = serializer.validated_data.get('follow_external_links', False)
            
            # Проверяем доступ к веб-сайту
            website = get_object_or_404(
                Website, 
                id=website_id, 
                created_by=request.user
            )
            
            # Запускаем фоновую задачу
            task = crawl_website_task.delay(
                str(website_id),
                crawl_depth,
                follow_external
            )
            
            logger.info(f"Запущено сканирование {website.url}, задача: {task.id}")
            
            return Response({
                'message': 'Сканирование запущено',
                'task_id': task.id,
                'website': {
                    'id': str(website.id),
                    'url': website.url,
                    'domain': website.domain
                },
                'settings': {
                    'crawl_depth': crawl_depth,
                    'follow_external_links': follow_external
                }
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Ошибка запуска сканирования: {str(e)}")
            return Response(
                {'error': 'Ошибка запуска сканирования', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CrawlStatusView(APIView):
    """
    API для проверки статуса сканирования
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        """
        Получение статуса задачи сканирования
        
        GET /api/v1/crawler/status/<task_id>/
        """
        try:
            # Получаем результат задачи
            task_result = AsyncResult(task_id)
            
            response_data = {
                'task_id': task_id,
                'status': task_result.status,
                'ready': task_result.ready()
            }
            
            if task_result.ready():
                if task_result.successful():
                    response_data['result'] = task_result.result
                else:
                    response_data['error'] = str(task_result.info)
            else:
                # Задача еще выполняется
                if task_result.info:
                    response_data['progress'] = task_result.info
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса задачи {task_id}: {str(e)}")
            return Response(
                {'error': 'Ошибка получения статуса', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 