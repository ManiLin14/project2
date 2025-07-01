"""
Модуль для шифрования файлов архивов
"""
import os
import json
from typing import Dict, Any
from django.conf import settings
from .aes_cipher import AESCipher


class ArchiveFileEncryption:
    """
    Класс для шифрования файлов архивов и метаданных
    """
    
    def __init__(self):
        """
        Инициализация шифровальщика архивов
        """
        self.cipher = AESCipher()
        
    def encrypt_archive_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Шифрование метаданных архива
        
        Args:
            metadata: Словарь с метаданными
            
        Returns:
            str: Зашифрованные метаданные
        """
        metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
        return self.cipher.encrypt(metadata_json)
    
    def decrypt_archive_metadata(self, encrypted_metadata: str) -> Dict[str, Any]:
        """
        Дешифрование метаданных архива
        
        Args:
            encrypted_metadata: Зашифрованные метаданные
            
        Returns:
            Dict[str, Any]: Расшифрованные метаданные
        """
        decrypted_json = self.cipher.decrypt(encrypted_metadata)
        return json.loads(decrypted_json)
    
    def encrypt_html_content(self, html_content: str) -> str:
        """
        Шифрование HTML контента страницы
        
        Args:
            html_content: HTML контент
            
        Returns:
            str: Зашифрованный контент
        """
        return self.cipher.encrypt(html_content)
    
    def decrypt_html_content(self, encrypted_content: str) -> str:
        """
        Дешифрование HTML контента
        
        Args:
            encrypted_content: Зашифрованный контент
            
        Returns:
            str: Расшифрованный HTML
        """
        return self.cipher.decrypt(encrypted_content)
    
    def create_secure_archive_directory(self, archive_id: str) -> str:
        """
        Создание безопасной директории для архива
        
        Args:
            archive_id: ID архива
            
        Returns:
            str: Путь к созданной директории
        """
        archive_dir = os.path.join(settings.ARCHIVE_ROOT, archive_id)
        os.makedirs(archive_dir, exist_ok=True)
        
        # Создаем поддиректории
        os.makedirs(os.path.join(archive_dir, 'pages'), exist_ok=True)
        os.makedirs(os.path.join(archive_dir, 'assets'), exist_ok=True)
        os.makedirs(os.path.join(archive_dir, 'screenshots'), exist_ok=True)
        
        return archive_dir
    
    def save_encrypted_page(self, archive_dir: str, url: str, html_content: str, 
                          timestamp: str) -> str:
        """
        Сохранение зашифрованной страницы
        
        Args:
            archive_dir: Директория архива
            url: URL страницы
            html_content: HTML контент
            timestamp: Метка времени
            
        Returns:
            str: Путь к сохраненному файлу
        """
        # Генерируем безопасное имя файла
        safe_filename = url.replace('://', '_').replace('/', '_').replace('?', '_')
        safe_filename = f"{safe_filename}_{timestamp}.html.enc"
        
        file_path = os.path.join(archive_dir, 'pages', safe_filename)
        
        # Шифруем контент
        encrypted_content = self.encrypt_html_content(html_content)
        
        # Сохраняем зашифрованный файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(encrypted_content)
            
        return file_path
    
    def load_encrypted_page(self, file_path: str) -> str:
        """
        Загрузка и дешифрование страницы
        
        Args:
            file_path: Путь к зашифрованному файлу
            
        Returns:
            str: Расшифрованный HTML контент
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            encrypted_content = f.read()
            
        return self.decrypt_html_content(encrypted_content) 