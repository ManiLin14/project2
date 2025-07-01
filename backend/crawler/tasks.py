"""
Celery задачи для фонового краулинга
"""
import asyncio
import os
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from archive.models import Website, ArchiveSnapshot, ArchivedPage, ArchivedAsset
from encryption.file_encryption import ArchiveFileEncryption
from .scrapling_crawler import WebArchiveCrawler
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def crawl_website_task(self, website_id: str, crawl_depth: int = 3, follow_external: bool = False):
    """
    Фоновая задача для сканирования веб-сайта
    
    Args:
        website_id: ID веб-сайта
        crawl_depth: Глубина сканирования
        follow_external: Следовать ли за внешними ссылками
        
    Returns:
        dict: Результаты сканирования
    """
    try:
        # Получаем веб-сайт
        website = Website.objects.get(id=website_id)
        
        # Создаем снапшот
        snapshot = ArchiveSnapshot.objects.create(
            website=website,
            status='processing'
        )
        
        logger.info(f"Начинаем сканирование {website.url}")
        
        # Создаем краулер
        crawler = WebArchiveCrawler(
            max_depth=crawl_depth,
            max_pages=settings.CRAWLER_MAX_PAGES,
            delay=settings.CRAWLER_DELAY
        )
        
        # Запускаем сканирование в event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                crawler.crawl_website(website.url, follow_external)
            )
        finally:
            loop.close()
        
        # Создаем зашифрованное хранилище
        encryption = ArchiveFileEncryption()
        archive_dir = encryption.create_secure_archive_directory(str(snapshot.id))
        
        # Сохраняем страницы
        pages_saved = 0
        for page_data in results['pages']:
            try:
                # Сохраняем зашифрованную страницу
                file_path = encryption.save_encrypted_page(
                    archive_dir,
                    page_data['url'],
                    page_data['content'],
                    str(page_data['timestamp'])
                )
                
                # Создаем запись в БД
                archived_page = ArchivedPage.objects.create(
                    snapshot=snapshot,
                    url=page_data['url'],
                    title=page_data['title'][:500],  # Ограничиваем длину
                    content_size=page_data['content_size'],
                    content_hash=page_data['content_hash']
                )
                
                # Устанавливаем зашифрованный контент через property
                archived_page.content = page_data['content']
                archived_page.save()
                
                pages_saved += 1
                
            except Exception as e:
                logger.error(f"Ошибка сохранения страницы {page_data['url']}: {str(e)}")
        
        # Сохраняем ресурсы
        assets_saved = 0
        for asset_data in results['assets']:
            try:
                # Определяем тип ресурса
                asset_type = asset_data['type']
                if asset_type == 'image':
                    asset_type_db = 'image'
                elif asset_type == 'css':
                    asset_type_db = 'css'
                elif asset_type == 'js':
                    asset_type_db = 'js'
                else:
                    asset_type_db = 'other'
                
                # Создаем запись о ресурсе
                ArchivedAsset.objects.create(
                    snapshot=snapshot,
                    url=asset_data['url'],
                    asset_type=asset_type_db,
                    file_path='',  # Будет заполнено при скачивании ресурса
                    file_size=0
                )
                
                assets_saved += 1
                
            except Exception as e:
                logger.error(f"Ошибка сохранения ресурса {asset_data['url']}: {str(e)}")
        
        # Сохраняем метаданные
        metadata = {
            'crawl_settings': results['settings'],
            'crawl_time': results['crawl_time'],
            'start_url': results['start_url'],
            'base_domain': results['base_domain']
        }
        
        encrypted_metadata = encryption.encrypt_archive_metadata(metadata)
        
        # Обновляем снапшот
        snapshot.status = 'completed'
        snapshot.pages_count = pages_saved
        snapshot.assets_count = assets_saved
        snapshot._encrypted_metadata = encrypted_metadata
        snapshot.save()
        
        logger.info(f"Сканирование завершено: {pages_saved} страниц, {assets_saved} ресурсов")
        
        return {
            'status': 'completed',
            'snapshot_id': str(snapshot.id),
            'pages_count': pages_saved,
            'assets_count': assets_saved,
            'crawl_time': results['crawl_time']
        }
        
    except Website.DoesNotExist:
        logger.error(f"Веб-сайт {website_id} не найден")
        return {'status': 'error', 'message': 'Веб-сайт не найден'}
        
    except Exception as e:
        logger.error(f"Ошибка сканирования: {str(e)}")
        
        # Обновляем статус снапшота при ошибке
        try:
            snapshot.status = 'failed'
            snapshot.save()
        except:
            pass
            
        return {'status': 'error', 'message': str(e)}


@shared_task
def download_asset_task(asset_id: str):
    """
    Фоновая задача для скачивания ресурса
    
    Args:
        asset_id: ID ресурса для скачивания
        
    Returns:
        dict: Результат скачивания
    """
    try:
        asset = ArchivedAsset.objects.get(id=asset_id)
        
        # Используем Scrapling для скачивания ресурса
        fetcher = StealthyFetcher()
        response = fetcher.fetch(asset.url)
        
        if response and response.status == 200:
            # Создаем путь для сохранения
            archive_dir = os.path.join(
                settings.ARCHIVE_ROOT, 
                str(asset.snapshot.id),
                'assets'
            )
            
            # Генерируем безопасное имя файла
            safe_filename = asset.url.replace('://', '_').replace('/', '_')
            file_path = os.path.join(archive_dir, safe_filename)
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Обновляем информацию о ресурсе
            asset.file_path = file_path
            asset.file_size = len(response.content)
            asset.content_type = response.headers.get('content-type', '')
            asset.save()
            
            return {
                'status': 'completed',
                'asset_id': str(asset.id),
                'file_size': asset.file_size
            }
        else:
            return {
                'status': 'error',
                'message': f'HTTP {response.status if response else "No response"}'
            }
            
    except ArchivedAsset.DoesNotExist:
        return {'status': 'error', 'message': 'Ресурс не найден'}
        
    except Exception as e:
        logger.error(f"Ошибка скачивания ресурса {asset_id}: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_snapshots_task():
    """
    Задача для очистки старых снапшотов
    """
    try:
        # Удаляем снапшоты старше 1 года (можно настроить)
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=365)
        
        old_snapshots = ArchiveSnapshot.objects.filter(
            snapshot_date__lt=cutoff_date,
            status__in=['completed', 'failed']
        )
        
        deleted_count = 0
        for snapshot in old_snapshots:
            try:
                # Удаляем файлы архива
                archive_dir = os.path.join(settings.ARCHIVE_ROOT, str(snapshot.id))
                if os.path.exists(archive_dir):
                    import shutil
                    shutil.rmtree(archive_dir)
                
                # Удаляем запись из БД
                snapshot.delete()
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка удаления снапшота {snapshot.id}: {str(e)}")
        
        logger.info(f"Удалено {deleted_count} старых снапшотов")
        return {'status': 'completed', 'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error(f"Ошибка очистки старых снапшотов: {str(e)}")
 