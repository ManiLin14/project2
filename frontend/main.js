/**
 * Главный JavaScript модуль для веб-архива
 * Управляет интерфейсом и взаимодействием с API
 */

// Класс для работы с API
class WebArchiveAPI {
    constructor() {
        this.baseUrl = '/api/v1';
    }

    // Получение CSRF токена
    async getCSRFToken() {
        try {
            const response = await fetch('/admin/');
            const html = await response.text();
            const match = html.match(/name=['"]csrfmiddlewaretoken['"] value=['"](.+?)['"]>/);
            return match ? match[1] : '';
        } catch (error) {
            console.error('Ошибка получения CSRF токена:', error);
            return '';
        }
    }

    // Универсальный метод для API запросов
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultHeaders = {
            'Content-Type': 'application/json',
        };

        // Добавляем CSRF токен только для POST/PUT/DELETE запросов
        if (options.method && options.method !== 'GET') {
            defaultHeaders['X-CSRFToken'] = await this.getCSRFToken();
        }

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
    async getWebsites() {
        return this.request('/archive/websites/');
    }

    // Получить снепшоты веб-сайта
    async getWebsiteSnapshots(websiteId) {
        return this.request(`/archive/websites/${websiteId}/snapshots/`);
    }

    // Получить снепшоты по дате
    async getSnapshotsByDate(websiteId, year, month, day) {
        let params = new URLSearchParams();
        if (year) params.append('year', year.toString());
        if (month) params.append('month', month.toString());
        if (day) params.append('day', day.toString());
        
        const query = params.toString() ? `?${params}` : '';
        return this.request(`/archive/websites/${websiteId}/snapshots_by_date/${query}`);
    }

    // Получить страницы снепшота
    async getSnapshotPages(snapshotId) {
        return this.request(`/archive/snapshots/${snapshotId}/pages/`);
    }

    // Получить контент страницы
    async getPageContent(pageId) {
        return this.request(`/archive/pages/${pageId}/content/`);
    }

    // Начать архивирование сайта
    async startArchiving(url) {
        return this.request('/crawler/start/', {
            method: 'POST',
            body: JSON.stringify({ url }),
        });
    }

    // Проверить статус архивирования
    async getArchivingStatus(taskId) {
        return this.request(`/crawler/status/${taskId}/`);
    }
}

// Главный класс приложения
class WebArchiveApp {
    constructor() {
        this.api = new WebArchiveAPI();
        this.currentModal = null;
        this.init();
    }

    // Инициализация приложения
    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    // Настройка обработчиков событий
    setupEventListeners() {
        console.log('Настройка обработчиков событий...');
        
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
        const urlInput = document.getElementById('urlInput');
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
    async loadInitialData() {
        console.log('Загрузка начальных данных...');
        try {
            await this.loadRecentArchives();
            await this.loadStatistics();
        } catch (error) {
            console.error('Ошибка загрузки данных:', error);
            this.showError('Ошибка подключения к серверу');
        }
    }

    // Загрузка недавних архивов
    async loadRecentArchives() {
        try {
            const response = await this.api.getWebsites();
            const websites = response.results ? response.results.slice(0, 6) : []; // Показываем последние 6
            
            const container = document.getElementById('recentArchives');
            if (container) {
                if (websites.length === 0) {
                    container.innerHTML = '<p class="no-data">Архивы пока не созданы. Добавьте первый сайт!</p>';
                } else {
                    container.innerHTML = websites.map(website => this.createArchiveCard(website)).join('');
                }
            }
        } catch (error) {
            console.error('Ошибка загрузки архивов:', error);
            const container = document.getElementById('recentArchives');
            if (container) {
                container.innerHTML = '<p class="error">Ошибка загрузки архивов</p>';
            }
        }
    }

    // Создание карточки архива
    createArchiveCard(website) {
        return `
            <div class="archive-card" onclick="app.showArchiveDetails('${website.id}')">
                <div class="archive-header">
                    <h3>${website.title || website.url}</h3>
                    <span class="status ${website.status}">${this.getStatusText(website.status)}</span>
                </div>
                <p class="archive-url">${website.url}</p>
                <div class="archive-stats">
                    <span>Снепшотов: ${website.snapshots_count || 0}</span>
                    <span>Создан: ${new Date(website.created_at).toLocaleDateString('ru-RU')}</span>
                </div>
            </div>
        `;
    }

    // Получение текста статуса
    getStatusText(status) {
        const statusTexts = {
            'pending': 'Ожидание',
            'processing': 'Обработка',
            'completed': 'Завершено',
            'failed': 'Ошибка'
        };
        return statusTexts[status] || status;
    }

    // Загрузка статистики
    async loadStatistics() {
        try {
            const response = await this.api.getWebsites();
            const totalSites = response.count || 0;
            
            // Подсчет снепшотов и страниц (примерно)
            let totalSnapshots = 0;
            let totalPages = 0;
            
            if (response.results) {
                response.results.forEach(website => {
                    totalSnapshots += website.snapshots_count || 0;
                });
            }
            
            this.updateStatElement('totalSites', totalSites);
            this.updateStatElement('totalSnapshots', totalSnapshots);
            this.updateStatElement('totalPages', totalPages);
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
            this.updateStatElement('totalSites', 0);
            this.updateStatElement('totalSnapshots', 0);
            this.updateStatElement('totalPages', 0);
        }
    }

    // Обновление элемента статистики
    updateStatElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value.toLocaleString('ru-RU');
        }
    }

    // Обработка клика по кнопке архивирования
    async handleArchiveClick() {
        const urlInput = document.getElementById('urlInput');
        const url = urlInput?.value.trim();
        
        if (!url) {
            this.showError('Введите URL для архивирования');
            return;
        }
        
        if (!this.isValidUrl(url)) {
            this.showError('Введите корректный URL (например: https://example.com)');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await this.api.startArchiving(url);
            this.hideLoading();
            this.showSuccess('Архивирование началось! Проверьте статус через несколько минут.');
            urlInput.value = '';
            
            // Обновляем список архивов
            setTimeout(() => this.loadRecentArchives(), 2000);
        } catch (error) {
            this.hideLoading();
            console.error('Ошибка архивирования:', error);
            this.showError('Ошибка при запуске архивирования: ' + error.message);
        }
    }

    // Обработка поиска
    async handleSearchClick() {
        const searchInput = document.getElementById('searchInput');
        const query = searchInput?.value.trim();
        
        if (!query) {
            this.showError('Введите запрос для поиска');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await this.api.getWebsites();
            const filteredWebsites = response.results ? response.results.filter(website =>
                website.url.toLowerCase().includes(query.toLowerCase()) ||
                (website.title && website.title.toLowerCase().includes(query.toLowerCase()))
            ) : [];
            
            this.hideLoading();
            this.showSearchResults(filteredWebsites);
        } catch (error) {
            this.hideLoading();
            console.error('Ошибка поиска:', error);
            this.showError('Ошибка при поиске: ' + error.message);
        }
    }

    // Показ результатов поиска
    showSearchResults(websites) {
        const modal = document.getElementById('archiveModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalContent = document.getElementById('modalContent');
        
        if (modal && modalTitle && modalContent) {
            modalTitle.textContent = `Результаты поиска (${websites.length})`;
            
            if (websites.length === 0) {
                modalContent.innerHTML = '<p>Ничего не найдено</p>';
            } else {
                modalContent.innerHTML = websites.map(website => this.createArchiveCard(website)).join('');
            }
            
            modal.style.display = 'block';
            this.currentModal = modal;
        }
    }

    // Показ деталей архива
    async showArchiveDetails(websiteId) {
        this.showLoading();
        
        try {
            const snapshots = await this.api.getWebsiteSnapshots(websiteId);
            
            const modal = document.getElementById('archiveModal');
            const modalTitle = document.getElementById('modalTitle');
            const modalContent = document.getElementById('modalContent');
            
            if (modal && modalTitle && modalContent) {
                modalTitle.textContent = 'Снепшоты архива';
                
                if (snapshots.length === 0) {
                    modalContent.innerHTML = '<p>Снепшоты не найдены</p>';
                } else {
                    modalContent.innerHTML = snapshots.map(snapshot => `
                        <div class="snapshot-card">
                            <h4>Снепшот от ${new Date(snapshot.created_at).toLocaleString('ru-RU')}</h4>
                            <p>Статус: ${this.getStatusText(snapshot.status)}</p>
                            <p>Страниц: ${snapshot.pages_count || 0}</p>
                            <p>Размер: ${this.formatSize(snapshot.total_size || 0)}</p>
                        </div>
                    `).join('');
                }
                
                modal.style.display = 'block';
                this.currentModal = modal;
            }
            
            this.hideLoading();
        } catch (error) {
            this.hideLoading();
            console.error('Ошибка загрузки деталей:', error);
            this.showError('Ошибка загрузки деталей архива: ' + error.message);
        }
    }

    // Закрытие модального окна
    closeModal() {
        if (this.currentModal) {
            this.currentModal.style.display = 'none';
            this.currentModal = null;
        }
    }

    // Форматирование размера файла
    formatSize(bytes) {
        if (bytes === 0) return '0 Б';
        const k = 1024;
        const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Проверка валидности URL
    isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }

    // Показ загрузки
    showLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'flex';
        }
    }

    // Скрытие загрузки
    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    // Показ ошибки
    showError(message) {
        console.error('Ошибка:', message);
        alert('Ошибка: ' + message);
    }

    // Показ успеха
    showSuccess(message) {
        console.log('Успех:', message);
        alert('Успех: ' + message);
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, инициализация приложения...');
    window.app = new WebArchiveApp();
}); 