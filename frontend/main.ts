/**
 * Главный TypeScript модуль для веб-архива
 * Управляет интерфейсом и взаимодействием с API
 */

// Типы данных
interface Website {
    id: string;
    url: string;
    title: string;
    created_at: string;
    status: string;
    snapshots_count: number;
    last_snapshot: string | null;
}

interface ArchiveSnapshot {
    id: string;
    created_at: string;
    status: string;
    pages_count: number;
    total_size: number;
    website: string;
}

interface ArchivedPage {
    id: string;
    url: string;
    title: string;
    status_code: number;
    content_type: string;
    size: number;
    created_at: string;
    snapshot: string;
}

interface ApiResponse<T> {
    results: T[];
    count: number;
    next: string | null;
    previous: string | null;
}

// Класс для работы с API
class WebArchiveAPI {
    private baseUrl: string;

    constructor() {
        this.baseUrl = '/api/v1';
    }

    // Получение CSRF токена
    private async getCSRFToken(): Promise<string> {
        const response = await fetch('/admin/');
        const html = await response.text();
        const match = html.match(/name=['"]csrfmiddlewaretoken['"] value=['"](.+?)['"]>/);
        return match ? match[1] : '';
    }

    // Универсальный метод для API запросов
    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultHeaders = {
            'Content-Type': 'application/json',
            'X-CSRFToken': await this.getCSRFToken(),
        };

        const response = await fetch(url, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    // Получить все веб-сайты
    async getWebsites(): Promise<ApiResponse<Website>> {
        return this.request<ApiResponse<Website>>('/archive/websites/');
    }

    // Получить снепшоты веб-сайта
    async getWebsiteSnapshots(websiteId: string): Promise<ArchiveSnapshot[]> {
        return this.request<ArchiveSnapshot[]>(`/archive/websites/${websiteId}/snapshots/`);
    }

    // Получить снепшоты по дате
    async getSnapshotsByDate(websiteId: string, year?: number, month?: number, day?: number): Promise<ArchiveSnapshot[]> {
        let params = new URLSearchParams();
        if (year) params.append('year', year.toString());
        if (month) params.append('month', month.toString());
        if (day) params.append('day', day.toString());
        
        const query = params.toString() ? `?${params}` : '';
        return this.request<ArchiveSnapshot[]>(`/archive/websites/${websiteId}/snapshots_by_date/${query}`);
    }

    // Получить страницы снепшота
    async getSnapshotPages(snapshotId: string): Promise<ArchivedPage[]> {
        return this.request<ArchivedPage[]>(`/archive/snapshots/${snapshotId}/pages/`);
    }

    // Получить контент страницы
    async getPageContent(pageId: string): Promise<any> {
        return this.request<any>(`/archive/pages/${pageId}/content/`);
    }

    // Начать архивирование сайта
    async startArchiving(url: string): Promise<any> {
        return this.request<any>('/crawler/start/', {
            method: 'POST',
            body: JSON.stringify({ url }),
        });
    }

    // Проверить статус архивирования
    async getArchivingStatus(taskId: string): Promise<any> {
        return this.request<any>(`/crawler/status/${taskId}/`);
    }
}

// Главный класс приложения
class WebArchiveApp {
    private api: WebArchiveAPI;
    private currentModal: HTMLElement | null = null;

    constructor() {
        this.api = new WebArchiveAPI();
        this.init();
    }

    // Инициализация приложения
    private init(): void {
        this.setupEventListeners();
        this.loadInitialData();
    }

    // Настройка обработчиков событий
    private setupEventListeners(): void {
        // Кнопка архивирования
        const archiveBtn = document.getElementById('archiveBtn');
        if (archiveBtn) {
            archiveBtn.addEventListener('click', () => this.handleArchiveClick());
        }

        // Кнопка поиска
        const searchBtn = document.getElementById('searchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.handleSearchClick());
        }

        // Enter в поле ввода URL
        const urlInput = document.getElementById('urlInput') as HTMLInputElement;
        if (urlInput) {
            urlInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleArchiveClick();
                }
            });
        }

        // Закрытие модального окна
        const modalClose = document.getElementById('modalClose');
        if (modalClose) {
            modalClose.addEventListener('click', () => this.closeModal());
        }

        // Закрытие модального окна по клику вне его
        const modal = document.getElementById('archiveModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }
    }

    // Загрузка начальных данных
    private async loadInitialData(): Promise<void> {
        try {
            await this.loadRecentArchives();
            await this.loadStatistics();
        } catch (error) {
            console.error('Ошибка загрузки данных:', error);
            this.showError('Ошибка подключения к серверу');
        }
    }

    // Загрузка недавних архивов
    private async loadRecentArchives(): Promise<void> {
        try {
            const response = await this.api.getWebsites();
            const websites = response.results.slice(0, 6); // Показываем последние 6
            
            const container = document.getElementById('recentArchives');
            if (container) {
                container.innerHTML = websites.map(website => this.createArchiveCard(website)).join('');
                
                // Добавляем обработчики клика
                container.querySelectorAll('.archive-card').forEach((card, index) => {
                    card.addEventListener('click', () => this.showArchiveDetails(websites[index]));
                });
            }
        } catch (error) {
            console.error('Ошибка загрузки архивов:', error);
        }
    }

    // Создание карточки архива
    private createArchiveCard(website: Website): string {
        const date = new Date(website.created_at).toLocaleDateString('ru-RU');
        const lastSnapshot = website.last_snapshot 
            ? new Date(website.last_snapshot).toLocaleDateString('ru-RU')
            : 'Нет снепшотов';

        return `
            <div class="archive-card" data-id="${website.id}">
                <div class="archive-url">${website.url}</div>
                <div class="archive-date">Добавлен: ${date}</div>
                <div class="archive-date">Последний снепшот: ${lastSnapshot}</div>
                <div class="archive-stats">
                    <span>📊 ${website.snapshots_count} снепшотов</span>
                    <span>📄 Статус: ${this.getStatusText(website.status)}</span>
                </div>
            </div>
        `;
    }

    // Получение текста статуса
    private getStatusText(status: string): string {
        const statusMap: { [key: string]: string } = {
            'pending': 'Ожидание',
            'processing': 'Обработка',
            'completed': 'Завершено',
            'failed': 'Ошибка'
        };
        return statusMap[status] || status;
    }

    // Загрузка статистики
    private async loadStatistics(): Promise<void> {
        try {
            const response = await this.api.getWebsites();
            const websites = response.results;
            
            // Подсчёт статистики
            let totalSnapshots = 0;
            let totalPages = 0;
            
            websites.forEach(website => {
                totalSnapshots += website.snapshots_count;
            });

            // Обновление отображения
            this.updateStatElement('totalSites', websites.length);
            this.updateStatElement('totalSnapshots', totalSnapshots);
            this.updateStatElement('totalPages', totalPages);
            
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        }
    }

    // Обновление элемента статистики
    private updateStatElement(elementId: string, value: number): void {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value.toLocaleString('ru-RU');
        }
    }

    // Обработка клика по кнопке архивирования
    private async handleArchiveClick(): Promise<void> {
        const urlInput = document.getElementById('urlInput') as HTMLInputElement;
        const url = urlInput.value.trim();

        if (!url) {
            this.showError('Введите URL сайта');
            return;
        }

        if (!this.isValidUrl(url)) {
            this.showError('Введите корректный URL');
            return;
        }

        try {
            this.showLoading();
            const result = await this.api.startArchiving(url);
            
            // Показываем результат
            this.showSuccess(`Архивирование начато! ID задачи: ${result.task_id}`);
            
            // Обновляем данные
            await this.loadRecentArchives();
            await this.loadStatistics();
            
        } catch (error) {
            console.error('Ошибка архивирования:', error);
            this.showError('Ошибка при запуске архивирования');
        } finally {
            this.hideLoading();
        }
    }

    // Обработка клика по кнопке поиска
    private async handleSearchClick(): Promise<void> {
        const urlInput = document.getElementById('urlInput') as HTMLInputElement;
        const url = urlInput.value.trim();

        if (!url) {
            this.showError('Введите URL для поиска');
            return;
        }

        try {
            this.showLoading();
            const response = await this.api.getWebsites();
            const websites = response.results.filter(website => 
                website.url.toLowerCase().includes(url.toLowerCase())
            );

            this.showSearchResults(websites);
            
        } catch (error) {
            console.error('Ошибка поиска:', error);
            this.showError('Ошибка при поиске');
        } finally {
            this.hideLoading();
        }
    }

    // Показ результатов поиска
    private showSearchResults(websites: Website[]): void {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContainer = document.getElementById('resultsContainer');
        
        if (resultsSection && resultsContainer) {
            resultsSection.style.display = 'block';
            
            if (websites.length === 0) {
                resultsContainer.innerHTML = '<p>Архивы не найдены</p>';
            } else {
                resultsContainer.innerHTML = `
                    <div class="archives-grid">
                        ${websites.map(website => this.createArchiveCard(website)).join('')}
                    </div>
                `;
                
                // Добавляем обработчики клика
                resultsContainer.querySelectorAll('.archive-card').forEach((card, index) => {
                    card.addEventListener('click', () => this.showArchiveDetails(websites[index]));
                });
            }
        }
    }

    // Показ деталей архива
    private async showArchiveDetails(website: Website): Promise<void> {
        try {
            const snapshots = await this.api.getWebsiteSnapshots(website.id);
            
            const modal = document.getElementById('archiveModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalUrl = document.getElementById('modalUrl');
            const modalDate = document.getElementById('modalDate');
            const modalStatus = document.getElementById('modalStatus');
            const modalTimeline = document.getElementById('modalTimeline');
            
            if (modal && modalTitle && modalUrl && modalDate && modalStatus && modalTimeline) {
                modalTitle.textContent = website.title || website.url;
                modalUrl.textContent = website.url;
                modalDate.textContent = new Date(website.created_at).toLocaleString('ru-RU');
                modalStatus.textContent = this.getStatusText(website.status);
                
                // Создание временной шкалы
                modalTimeline.innerHTML = `
                    <h4>Снепшоты (${snapshots.length})</h4>
                    <div class="timeline">
                        ${snapshots.map(snapshot => `
                            <div class="timeline-item" data-snapshot-id="${snapshot.id}">
                                <div class="timeline-date">${new Date(snapshot.created_at).toLocaleString('ru-RU')}</div>
                                <div class="timeline-info">
                                    ${snapshot.pages_count} страниц • ${this.formatSize(snapshot.total_size)}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
                
                modal.style.display = 'flex';
                this.currentModal = modal;
            }
            
        } catch (error) {
            console.error('Ошибка загрузки деталей:', error);
            this.showError('Ошибка загрузки деталей архива');
        }
    }

    // Закрытие модального окна
    private closeModal(): void {
        if (this.currentModal) {
            this.currentModal.style.display = 'none';
            this.currentModal = null;
        }
    }

    // Форматирование размера файла
    private formatSize(bytes: number): string {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Проверка валидности URL
    private isValidUrl(url: string): boolean {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    // Показ загрузки
    private showLoading(): void {
        const loadingSpinner = document.getElementById('loadingSpinner');
        const resultsSection = document.getElementById('resultsSection');
        
        if (loadingSpinner && resultsSection) {
            resultsSection.style.display = 'block';
            loadingSpinner.style.display = 'block';
        }
    }

    // Скрытие загрузки
    private hideLoading(): void {
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }

    // Показ ошибки
    private showError(message: string): void {
        // Простое уведомление об ошибке
        alert(`Ошибка: ${message}`);
    }

    // Показ успеха
    private showSuccess(message: string): void {
        // Простое уведомление об успехе
        alert(`Успех: ${message}`);
    }
}

// Инициализация приложения после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    new WebArchiveApp();
}); 