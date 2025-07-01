"""
Админ-панель для веб-архива
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Website, ArchiveSnapshot, ArchivedPage, ArchivedAsset


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    """
    Админ для веб-сайтов
    """
    list_display = ['domain', 'title', 'created_by', 'is_active', 'created_at', 'snapshots_count']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['domain', 'title', 'url']
    readonly_fields = ['id', 'created_at']
    
    def snapshots_count(self, obj):
        """Количество снапшотов"""
        return obj.snapshots.count()
    snapshots_count.short_description = 'Снапшоты'


class ArchivedPageInline(admin.TabularInline):
    """
    Inline для архивированных страниц
    """
    model = ArchivedPage
    extra = 0
    readonly_fields = ['id', 'archived_at', 'content_size']
    fields = ['url', 'title', 'archived_at', 'content_size']


class ArchivedAssetInline(admin.TabularInline):
    """
    Inline для архивированных ресурсов
    """
    model = ArchivedAsset
    extra = 0
    readonly_fields = ['id', 'archived_at', 'file_size']
    fields = ['url', 'asset_type', 'archived_at', 'file_size']


@admin.register(ArchiveSnapshot)
class ArchiveSnapshotAdmin(admin.ModelAdmin):
    """
    Админ для снапшотов архивов
    """
    list_display = ['website', 'snapshot_date', 'status', 'pages_count', 'assets_count', 'total_size_mb']
    list_filter = ['status', 'snapshot_date', 'website__domain']
    search_fields = ['website__domain', 'website__title']
    readonly_fields = ['id', 'snapshot_date']
    inlines = [ArchivedPageInline, ArchivedAssetInline]
    
    def total_size_mb(self, obj):
        """Размер в МБ"""
        return f"{obj.total_size / 1024 / 1024:.2f} МБ"
    total_size_mb.short_description = 'Размер'


@admin.register(ArchivedPage)
class ArchivedPageAdmin(admin.ModelAdmin):
    """
    Админ для архивированных страниц
    """
    list_display = ['title', 'url', 'snapshot', 'archived_at', 'content_size_kb']
    list_filter = ['archived_at', 'snapshot__website__domain']
    search_fields = ['title', 'url']
    readonly_fields = ['id', 'archived_at', 'content_hash']
    
    def content_size_kb(self, obj):
        """Размер контента в КБ"""
        return f"{obj.content_size / 1024:.2f} КБ"
    content_size_kb.short_description = 'Размер'


@admin.register(ArchivedAsset)
class ArchivedAssetAdmin(admin.ModelAdmin):
    """
    Админ для архивированных ресурсов
    """
    list_display = ['asset_type', 'url', 'snapshot', 'archived_at', 'file_size_kb']
    list_filter = ['asset_type', 'archived_at', 'content_type']
    search_fields = ['url']
    readonly_fields = ['id', 'archived_at']
    
    def file_size_kb(self, obj):
        """Размер файла в КБ"""
        return f"{obj.file_size / 1024:.2f} КБ"
    file_size_kb.short_description = 'Размер' 