"""
Современный веб-краулер с использованием Scrapling
Поддерживает обход блокировок и извлечение контента для архивации
"""
import asyncio
import logging
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from pathlib import Path
import hashlib
import mimetypes
import re

try:
    from scrapling import Adaptor
except ImportError:
    # Fallback для тестирования
    class Adaptor:
        def __init__(self, *args, **kwargs):
            pass
        def get(self, url, **kwargs):
            return MockResponse()

class MockResponse:
    def __init__(self):
        self.text = "<html><body>Mock content</body></html>"
        self.content = b"Mock content"
        self.status_code = 200
        self.headers = {}

logger = logging.getLogger(__name__)


class WebArchiveCrawler:
    """
    Современный веб-краулер для архивации сайтов
    """
    
    def __init__(self, 
                 max_depth: int = 3,
                 max_pages: int = 100,
                 delay: float = 1.0,
                 timeout: int = 30,
                 proxy_list: Optional[List[str]] = None,
                 user_agent: Optional[str] = None):
        """
        Инициализация краулера
        
        Args:
            max_depth: Максимальная глубина сканирования
            max_pages: Максимальное количество страниц
            delay: Задержка между запросами (секунды)
            timeout: Таймаут запроса (секунды)
            proxy_list: Список прокси серверов
            user_agent: Пользовательский User-Agent
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.timeout = timeout
        self.proxy_list = proxy_list or []
        
        # Настройка Scrapling адаптера
        adaptor_config = {
            'auto_match': True,  # Автоматическое определение блокировок
            'stealth': True,     # Режим скрытности
            'debug': False
        }
        
        if user_agent:
            adaptor_config['headers'] = {'User-Agent': user_agent}
            
        self.adaptor = Adaptor(**adaptor_config)
        
        # Состояние краулера
        self.visited_urls: Set[str] = set()
        self.crawled_pages: List[Dict] = []
        self.errors: List[Dict] = []
        
        # Регулярные выражения для извлечения ресурсов
        self.css_url_pattern = re.compile(r'url\(["\']?([^"\')\s]+)["\']?\)', re.IGNORECASE)
        self.link_pattern = re.compile(r'<link[^>]+href=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)
        self.script_pattern = re.compile(r'<script[^>]+src=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)
        self.img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """Нормализация URL"""
        if not url:
            return ""
            
        # Удаление якорей и параметров запроса для архивации
        normalized = urljoin(base_url, url)
        parsed = urlparse(normalized)
        
        # Убираем фрагменты (#section)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Добавляем query параметры если они важны
        if parsed.query:
            # Фильтруем служебные параметры
            query_params = parse_qs(parsed.query)
            filtered_params = {k: v for k, v in query_params.items() 
                             if not k.startswith(('utm_', 'fb_', 'gclid'))}
            if filtered_params:
                query_string = '&'.join([f"{k}={v[0]}" for k, v in filtered_params.items()])
                normalized += f"?{query_string}"
        
        return normalized
    
    def is_same_domain(self, url: str, base_domain: str) -> bool:
        """Проверка принадлежности к тому же домену"""
        try:
            url_domain = urlparse(url).netloc
            return url_domain == base_domain or url_domain.endswith(f".{base_domain}")
        except:
            return False
    
    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """Извлечение ссылок из HTML"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        # Поиск ссылок в href атрибутах
        href_pattern = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)
        for match in href_pattern.finditer(html_content):
            url = self.normalize_url(match.group(1), base_url)
            if url and self.is_same_domain(url, base_domain):
                links.append(url)
        
        return list(set(links))  # Убираем дубликаты
    
    def extract_assets(self, html_content: str, base_url: str) -> Dict[str, List[str]]:
        """Извлечение статических ресурсов"""
        assets = {
            'css': [],
            'js': [],
            'images': [],
            'fonts': [],
            'other': []
        }
        
        base_domain = urlparse(base_url).netloc
        
        # CSS файлы
        for match in self.link_pattern.finditer(html_content):
            url = self.normalize_url(match.group(1), base_url)
            if url and ('css' in url.lower() or url.endswith('.css')):
                assets['css'].append(url)
        
        # JavaScript файлы
        for match in self.script_pattern.finditer(html_content):
            url = self.normalize_url(match.group(1), base_url)
            if url and url.endswith('.js'):
                assets['js'].append(url)
        
        # Изображения
        for match in self.img_pattern.finditer(html_content):
            url = self.normalize_url(match.group(1), base_url)
            if url:
                assets['images'].append(url)
        
        # URL из CSS
        for match in self.css_url_pattern.finditer(html_content):
            url = self.normalize_url(match.group(1), base_url)
            if url:
                # Определяем тип ресурса по расширению
                if any(ext in url.lower() for ext in ['.woff', '.woff2', '.ttf', '.otf']):
                    assets['fonts'].append(url)
                elif any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']):
                    assets['images'].append(url)
                else:
                    assets['other'].append(url)
        
        # Убираем дубликаты
        for asset_type in assets:
            assets[asset_type] = list(set(assets[asset_type]))
        
        return assets
    
    def fetch_page(self, url: str) -> Optional[Dict]:
        """Загрузка одной страницы"""
        try:
            logger.info(f"Crawling: {url}")
            
            # Выполняем запрос через Scrapling
            response = self.adaptor.get(url, timeout=self.timeout)
            
            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None
            
            # Извлекаем контент и метаданные
            html_content = response.text
            content_hash = hashlib.sha256(html_content.encode()).hexdigest()
            
            # Извлекаем заголовок страницы
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""
            
            # Извлекаем мета описание
            meta_desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\'][^>]*>', 
                                       html_content, re.IGNORECASE)
            description = meta_desc_match.group(1).strip() if meta_desc_match else ""
            
            # Извлекаем ссылки и ресурсы
            links = self.extract_links(html_content, url)
            assets = self.extract_assets(html_content, url)
            
            page_data = {
                'url': url,
                'title': title,
                'description': description,
                'html_content': html_content,
                'content_hash': content_hash,
                'links': links,
                'assets': assets,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'size': len(html_content.encode('utf-8'))
            }
            
            return page_data
            
        except Exception as e:
            error_data = {
                'url': url,
                'error': str(e),
                'error_type': type(e).__name__
            }
            self.errors.append(error_data)
            logger.error(f"Error crawling {url}: {e}")
            return None
    
    async def crawl_website(self, start_url: str) -> Dict:
        """
        Асинхронное сканирование сайта
        
        Args:
            start_url: Начальный URL для сканирования
            
        Returns:
            Словарь с результатами сканирования
        """
        logger.info(f"Starting crawl of {start_url}")
        
        # Инициализация
        self.visited_urls.clear()
        self.crawled_pages.clear()
        self.errors.clear()
        
        # Очередь URL для обработки
        url_queue = [(start_url, 0)]  # (url, depth)
        base_domain = urlparse(start_url).netloc
        
        while url_queue and len(self.crawled_pages) < self.max_pages:
            current_url, depth = url_queue.pop(0)
            
            # Проверяем ограничения
            if current_url in self.visited_urls or depth > self.max_depth:
                continue
            
            self.visited_urls.add(current_url)
            
            # Загружаем страницу
            page_data = self.fetch_page(current_url)
            if page_data:
                self.crawled_pages.append(page_data)
                
                # Добавляем новые ссылки в очередь
                if depth < self.max_depth:
                    for link in page_data['links']:
                        if (link not in self.visited_urls and 
                            self.is_same_domain(link, base_domain)):
                            url_queue.append((link, depth + 1))
            
            # Задержка между запросами
            if self.delay > 0:
                await asyncio.sleep(self.delay)
        
        # Формируем результат
        result = {
            'start_url': start_url,
            'pages_crawled': len(self.crawled_pages),
            'total_pages_found': len(self.visited_urls),
            'errors_count': len(self.errors),
            'pages': self.crawled_pages,
            'errors': self.errors,
            'crawl_stats': {
                'max_depth_reached': max([0] + [len(page['url'].split('/')) - 3 for page in self.crawled_pages]),
                'total_links_found': sum(len(page['links']) for page in self.crawled_pages),
                'total_assets_found': sum(
                    sum(len(assets) for assets in page['assets'].values()) 
                    for page in self.crawled_pages
                ),
                'avg_page_size': sum(page['size'] for page in self.crawled_pages) // max(1, len(self.crawled_pages))
            }
        }
        
        logger.info(f"Crawl completed: {result['pages_crawled']} pages, {result['errors_count']} errors")
        return result
    
    def download_asset(self, asset_url: str) -> Optional[Tuple[bytes, str]]:
        """
        Загрузка статического ресурса
        
        Returns:
            Кортеж (content, content_type) или None при ошибке
        """
        try:
            response = self.adaptor.get(asset_url, timeout=self.timeout)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 
                    mimetypes.guess_type(asset_url)[0] or 'application/octet-stream')
                return response.content, content_type
            else:
                logger.warning(f"HTTP {response.status_code} for asset {asset_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading asset {asset_url}: {e}")
            return None 