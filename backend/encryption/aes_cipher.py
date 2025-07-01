"""
AES 256 шифрование для безопасного хранения архивов
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from django.conf import settings


class AESCipher:
    """
    Класс для AES-256 шифрования/дешифрования данных
    """
    
    def __init__(self, password: str = None):
        """
        Инициализация AES шифровальщика
        
        Args:
            password: Пароль для генерации ключа
        """
        self.password = password or settings.AES_KEY
        
    def _derive_key(self, salt: bytes) -> bytes:
        """
        Генерация ключа из пароля и соли
        
        Args:
            salt: Соль для генерации ключа
            
        Returns:
            bytes: 256-битный ключ
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(self.password.encode())
        return key
    
    def encrypt(self, data: str) -> str:
        """
        Шифрование строки с помощью AES-256-CBC
        
        Args:
            data: Данные для шифрования
            
        Returns:
            str: Зашифрованные данные в формате base64
        """
        if not data:
            return ""
            
        # Генерируем случайную соль и IV
        salt = os.urandom(16)
        iv = os.urandom(16)
        
        # Получаем ключ
        key = self._derive_key(salt)
        
        # Создаем шифр
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Добавляем padding к данным
        data_bytes = data.encode('utf-8')
        padding_length = 16 - len(data_bytes) % 16
        padded_data = data_bytes + bytes([padding_length] * padding_length)
        
        # Шифруем данные
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Комбинируем соль, IV и зашифрованные данные
        encrypted_data = salt + iv + ciphertext
        
        # Возвращаем в формате base64
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Дешифрование данных
        
        Args:
            encrypted_data: Зашифрованные данные в формате base64
            
        Returns:
            str: Расшифрованные данные
        """
        if not encrypted_data:
            return ""
            
        try:
            # Декодируем из base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Извлекаем соль, IV и зашифрованные данные
            salt = encrypted_bytes[:16]
            iv = encrypted_bytes[16:32]
            ciphertext = encrypted_bytes[32:]
            
            # Получаем ключ
            key = self._derive_key(salt)
            
            # Создаем дешифровальщик
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            # Дешифруем данные
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Убираем padding
            padding_length = padded_data[-1]
            data = padded_data[:-padding_length]
            
            return data.decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"Ошибка дешифрования: {str(e)}")
    
    def encrypt_file(self, file_path: str, output_path: str = None) -> str:
        """
        Шифрование файла
        
        Args:
            file_path: Путь к исходному файлу
            output_path: Путь к зашифрованному файлу
            
        Returns:
            str: Путь к зашифрованному файлу
        """
        if not output_path:
            output_path = file_path + '.encrypted'
            
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        # Конвертируем в строку base64 для шифрования
        file_data_b64 = base64.b64encode(file_data).decode('utf-8')
        encrypted_data = self.encrypt(file_data_b64)
        
        with open(output_path, 'w') as f:
            f.write(encrypted_data)
            
        return output_path
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str = None) -> str:
        """
        Дешифрование файла
        
        Args:
            encrypted_file_path: Путь к зашифрованному файлу
            output_path: Путь к расшифрованному файлу
            
        Returns:
            str: Путь к расшифрованному файлу
        """
        if not output_path:
            output_path = encrypted_file_path.replace('.encrypted', '')
            
        with open(encrypted_file_path, 'r') as f:
            encrypted_data = f.read()
            
        decrypted_b64 = self.decrypt(encrypted_data)
        file_data = base64.b64decode(decrypted_b64.encode('utf-8'))
        
        with open(output_path, 'wb') as f:
            f.write(file_data)
            
        return output_path 