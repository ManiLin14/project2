"""
Сериализаторы для API веб-архива
"""
from rest_framework import serializers
from .models import Website, ArchiveSnapshot, ArchivedPage, ArchivedAsset


class WebsiteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для веб-сайтов
    """
    snapshots_count = serializers.SerializerMethodField()
    latest_snapshot = serializers.SerializerMethodField()
    
    class Meta:
        model = Website
        fields = [
            'id', 'url', 'domain', 'title', 'description',
            'created_at', 'is_active', 'crawl_depth',
            'snapshots_count', 'latest_snapshot'
        ]
        read_only_fields = ['id', 'created_at', 'domain']
    
    def get_snapshots_count(self, obj):
        """Количество снапшотов"""
        return obj.snapshots.count()
    
    def get_latest_snapshot(self, obj):
        """Последний снапшот"""
        latest = obj.snapshots.first()
        if latest:
            return {
                'id': latest.id,
                'snapshot_date': latest.snapshot_date,
                'status': latest.status,
                'pages_count': latest.pages_count
            }
        return None
    
    def create(self, validated_data):
        """Создание нового сайта"""
        # Извлекаем домен из URL
        url = validated_data['url']
        from urllib.parse import urlparse
        parsed = urlparse(url)
        validated_data['domain'] = parsed.netloc
        
        # Устанавливаем текущего пользователя
        validated_data['created_by'] = self.context['request'].user
        
        return super().create(validated_data)


class ArchivedPageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для архивированных страниц
    """
    content_size_kb = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchivedPage
        fields = [
            'id', 'url', 'title', 'archived_at',
            'content_size', 'content_size_kb', 'screenshot_path'
        ]
        read_only_fields = ['id', 'archived_at']
    
    def get_content_size_kb(self, obj):
        """Размер в КБ"""
        return round(obj.content_size / 1024, 2)


class ArchivedAssetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для архивированных ресурсов
    """
    file_size_kb = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchivedAsset
        fields = [
            'id', 'url', 'asset_type', 'file_size',
            'file_size_kb', 'content_type', 'archived_at'
        ]
        read_only_fields = ['id', 'archived_at']
    
    def get_file_size_kb(self, obj):
        """Размер в КБ"""
        return round(obj.file_size / 1024, 2)


class ArchiveSnapshotSerializer(serializers.ModelSerializer):
    """
    Сериализатор для снапшотов архивов
    """
    website_info = serializers.SerializerMethodField()
    total_size_mb = serializers.SerializerMethodField()
    pages = ArchivedPageSerializer(many=True, read_only=True)
    assets = ArchivedAssetSerializer(many=True, read_only=True)
    
    class Meta:
        model = ArchiveSnapshot
        fields = [
            'id', 'snapshot_date', 'status', 'pages_count',
            'assets_count', 'total_size', 'total_size_mb',
            'website_info', 'pages', 'assets'
        ]
        read_only_fields = ['id', 'snapshot_date']
    
    def get_website_info(self, obj):
        """Информация о сайте"""
        return {
            'id': obj.website.id,
            'domain': obj.website.domain,
            'title': obj.website.title,
            'url': obj.website.url
        }
    
    def get_total_size_mb(self, obj):
        """Размер в МБ"""
        return round(obj.total_size / 1024 / 1024, 2)


class ArchiveSnapshotListSerializer(serializers.ModelSerializer):
    """
    Упрощенный сериализатор для списка снапшотов
    """
    website_domain = serializers.CharField(source='website.domain')
    website_title = serializers.CharField(source='website.title')
    total_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = ArchiveSnapshot
        fields = [
            'id', 'snapshot_date', 'status', 'pages_count',
            'assets_count', 'total_size_mb', 'website_domain', 'website_title'
        ]
    
    def get_total_size_mb(self, obj):
        """Размер в МБ"""
        return round(obj.total_size / 1024 / 1024, 2)


class CreateSnapshotSerializer(serializers.Serializer):
    """
    Сериализатор для создания нового снапшота
    """
    website_id = serializers.UUIDField()
    crawl_depth = serializers.IntegerField(min_value=1, max_value=10, default=3)
    follow_external_links = serializers.BooleanField(default=False)
    
    def validate_website_id(self, value):
        """Проверка существования сайта"""
        try:
            website = Website.objects.get(id=value, created_by=self.context['request'].user)
            return value
        except Website.DoesNotExist:
            raise serializers.ValidationError("Сайт не найден или у вас нет к нему доступа") 