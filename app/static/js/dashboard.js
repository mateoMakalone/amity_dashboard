/**
 * Модернизированный Amity Metrics Dashboard
 * Поддержка секций, debug-режима, гибкой визуализации и экспорта отчётов
 */

// Глобальные переменные
let sectionsConfig = {};
let allMetrics = {};
let timeIntervals = [];
let currentInterval = 30; // минуты
let debugMode = false;
let updateTimer = null;
let isExporting = false;

let firstLoad = true;
// Форматирование чисел
const formatFunctions = {
    fixed0: x => x.toFixed(0),
    fixed1: x => x.toFixed(1),
    fixed2: x => x.toFixed(2),
    fixed3: x => x.toFixed(3),
    percent: x => Math.round(x * 100),
    mb: x => (x / 1024 / 1024).toFixed(1)
};

// --- Добавляем функцию нормализации id ---
function normalizeId(name) {
    return name.replace(/[^a-zA-Z0-9_-]/g, '_');
}

/**
 * Инициализация дашборда
 */
async function initDashboard() {
    console.log('🚀 Starting dashboard initialization...');
    try {
        // Проверяем debug-режим из URL
        const urlParams = new URLSearchParams(window.location.search);
        debugMode = urlParams.get('debug') === 'true';
        console.log('🔧 Debug mode:', debugMode);
        
        // Загружаем конфигурацию секций
        console.log('📋 Loading sections configuration...');
        await loadSectionsConfig();
        
        // Инициализируем интерфейс
        console.log('🎛️ Initializing controls...');
        initControls();
        
        // Загружаем данные
        console.log('📊 Loading sections data...');
        await loadSectionsData();
        
        // Запускаем автообновление
        console.log('⏰ Starting auto-update...');
        startAutoUpdate();
        
        // Скрываем индикатор загрузки
        console.log('✅ Dashboard initialization completed');
        hideLoading();
        
    } catch (error) {
        console.error('❌ Dashboard initialization failed:', error);
        console.error('Error stack:', error.stack);
        showError('Ошибка инициализации дашборда: ' + error.message);
        hideLoading();
    }
}

/**
 * Загружает конфигурацию секций и метрик
 */
async function loadSectionsConfig() {
    console.log('🔍 Fetching /api/sections...');
    try {
        const response = await fetch('/api/sections');
        console.log('📡 Response status:', response.status);
        console.log('📡 Response headers:', response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📋 Received sections config:', data);
        
        sectionsConfig = data.sections || {};
        allMetrics = data.all_metrics || {};
        timeIntervals = data.time_intervals || [];
        
        console.log('📊 Sections config loaded:', Object.keys(sectionsConfig));
        console.log('📈 All metrics count:', Object.keys(allMetrics).length);
        console.log('⏰ Time intervals:', timeIntervals);
        
        // Динамически заполняем селектор интервалов
        const intervalSelect = document.getElementById('time-interval');
        if (intervalSelect && timeIntervals.length > 0) {
            intervalSelect.innerHTML = '';
            timeIntervals.forEach(interval => {
                const option = document.createElement('option');
                option.value = interval.value;
                option.textContent = interval.label;
                intervalSelect.appendChild(option);
            });
            intervalSelect.value = currentInterval;
            console.log('⏰ Time interval selector updated');
        }
        
    } catch (error) {
        console.error('❌ Failed to load sections config:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            url: '/api/sections'
        });
        throw new Error('Не удалось загрузить конфигурацию секций: ' + error.message);
    }
}

/**
 * Инициализирует элементы управления
 */
function initControls() {
    // Селектор интервала времени
    const intervalSelect = document.getElementById('time-interval');
    if (intervalSelect) {
        intervalSelect.value = currentInterval;
        intervalSelect.addEventListener('change', async (e) => {
            currentInterval = parseInt(e.target.value);
            await loadSectionsData();
            startAutoUpdate(); // Перезапуск таймера после смены интервала
        });
    }
    
    // Кнопка debug
    const debugToggle = document.getElementById('debug-toggle');
    if (debugToggle) {
        debugToggle.classList.toggle('active', debugMode);
        debugToggle.addEventListener('click', toggleDebugMode);
    }
    
    // Кнопка экспорта
    const exportBtn = document.getElementById('export-report');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportReport);
    }
}

/**
 * Переключает debug-режим
 */
function toggleDebugMode() {
    debugMode = !debugMode;
    
    const debugToggle = document.getElementById('debug-toggle');
    if (debugToggle) {
        debugToggle.classList.toggle('active', debugMode);
    }
    
    // Обновляем URL
    const url = new URL(window.location);
    if (debugMode) {
        url.searchParams.set('debug', 'true');
    } else {
        url.searchParams.delete('debug');
    }
    window.history.replaceState({}, '', url);
    
    // Перезагружаем данные с debug-информацией
    loadSectionsData();
}

/**
 * Загружает данные для всех секций
 */
async function loadSectionsData() {
    console.log('📊 Starting to load sections data...');
    console.log('📋 Available sections:', Object.keys(sectionsConfig));
    
    try {
        const container = document.getElementById('sections-container');
        const isFirst = firstLoad && container;
        console.log('🔄 First load:', firstLoad, 'Container exists:', !!container);
        
        if (isFirst) {
            console.log('🔄 First load detected, showing loading indicator and rendering sections...');
            showLoading();
            updateStatus('loading');
            renderSections();
        } 
        
        // Загружаем все данные метрик одним batch запросом
        console.log('📥 Loading batch metrics data...');
        const batchData = await loadBatchMetricsData();
        
        // Обновляем данные для каждой секции
        console.log('📥 Updating sections with batch data...');
        const sectionPromises = Object.keys(sectionsConfig).map(async (sectionName) => {
            console.log(`📥 Updating section: ${sectionName}`);
            await updateSectionWithBatchData(sectionName, batchData);
        });
        
        await Promise.all(sectionPromises);
        console.log('✅ All sections updated successfully');
        
        updateStatus('ok');
        
    } catch (error) {
        console.error('❌ Failed to load sections data:', error);
        console.error('Error stack:', error.stack);
        showError('Ошибка загрузки данных: ' + error.message);
        updateStatus('error');
    } finally {
        if (firstLoad) {
            console.log('🔄 First load completed, hiding loading indicator');
            hideLoading();
            firstLoad = false;
        }
    }
}

/**
 * Загружает все данные метрик одним batch запросом
 */
async function loadBatchMetricsData() {
    console.log('📊 Loading batch metrics data...');
    
    const params = new URLSearchParams({
        interval: currentInterval.toString()
    });
    
    const url = `/api/metrics/batch/history?${params}`;
    console.log(`🔗 Fetching batch data from: ${url}`);
    
    try {
        const response = await fetch(url);
        console.log(`📡 Batch response status:`, response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`📊 Received batch data for ${Object.keys(data.data || {}).length} metrics`);
        
        return data.data || {};
        
    } catch (error) {
        console.error(`❌ Failed to load batch metrics data:`, error);
        throw error;
    }
}

/**
 * Обновляет секцию с batch данными
 */
async function updateSectionWithBatchData(sectionName, batchData) {
    const normId = normalizeId(sectionName);
    console.log(`📥 Updating section ${sectionName} with batch data`);
    
    try {
        const sectionMetrics = sectionsConfig[sectionName] || [];
        console.log(`📊 Section ${sectionName} has ${sectionMetrics.length} metrics:`, sectionMetrics);
        
        const content = document.getElementById(`section-content-${normId}`);
        console.log(`🎯 Section content element:`, content ? 'found' : 'not found');
        
        if (!content) {
            console.warn(`⚠️ Content element for section ${sectionName} not found`);
            return;
        }
        
        // Удаляем индикатор загрузки в секции
        const loadingIndicator = content.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
        
        // Если в секции нет метрик — показываем stub и выходим
        if (sectionMetrics.length === 0) {
            console.log(`📭 Section ${sectionName} has no metrics`);
            // Если ещё нет содержимого, создаём сообщение
            if (!content.hasChildNodes()) {
                content.innerHTML = '<div class="no-data">Нет метрик в этой секции</div>';
            }
            return;
        }
        
        // Обрабатываем метрики секции с batch данными
        console.log(`🔄 Processing ${sectionMetrics.length} metrics for section ${sectionName}`);
        
        sectionMetrics.forEach(metricId => {
            const metricData = batchData[metricId];
            const existingCard = document.getElementById(`metric-${metricId}`);
            
            if (existingCard) {
                console.log(`🔄 Updating existing card for metric: ${metricId}`);
                // Если карточка уже существует, обновляем её
                if (metricData && metricData.status === 'success') {
                    const config = allMetrics[metricId];
                    updateMetricCard(metricId, {
                        config: config,
                        history: metricData.data
                    });
                } else {
                    existingCard.innerHTML = `<div class="metric-header"><h4 class="metric-title">${metricId}</h4></div><div class="metric-error">Ошибка: Нет данных</div>`;
                }
            } else {
                console.log(`🆕 Creating new card for metric: ${metricId}`);
                // Если карточки нет, создаём новую и добавляем
                let error = null;
                let data = null;
                
                if (metricData && metricData.status === 'success') {
                    data = {
                        config: allMetrics[metricId],
                        history: metricData.data
                    };
                } else {
                    error = 'Нет данных';
                }
                
                const metricCard = createMetricCard(metricId, data, error);
                content.appendChild(metricCard);
                
                // Отрисовываем графики после добавления новой карточки
                if (data && data.history && data.history.result && data.history.result.length > 0) {
                    const config = data.config;
                    const history = data.history;
                    const resultObj = history.result[0];
                    if (resultObj.values && resultObj.values.length > 0) {
                        if (config.type.includes('trend')) {
                            renderTrendChart(config, resultObj.values, `trend-${metricId}`);
                        }
                    }
                }
            }
        });
        
        console.log(`✅ Section ${sectionName} updated successfully`);
        
    } catch (error) {
        console.error(`❌ Failed to update section ${sectionName}:`, error);
        console.error('Error stack:', error.stack);
        const content = document.getElementById(`section-content-${normId}`);
        if (content) {
            content.innerHTML = `<div class="metric-error">Ошибка обновления секции: ${error.message}</div>`;
        }
    }
}

/**
 * Рендерит секции на странице
 */
function renderSections() {
    console.log('🎨 Rendering sections...');
    const container = document.getElementById('sections-container');
    if (!container) {
        console.error('❌ Sections container not found');
        return;
    }
    
    console.log('📋 Available sections:', Object.keys(sectionsConfig));
    container.innerHTML = '';
    
    // Сортируем секции: KPI всегда первая
    const sectionNames = Object.keys(sectionsConfig);
    sectionNames.sort((a, b) => {
        if (a === 'KPI') return -1;
        if (b === 'KPI') return 1;
        return 0;
    });
    
    console.log('📊 Sorted section names:', sectionNames);
    
    sectionNames.forEach(sectionName => {
        console.log(`🎨 Creating section: ${sectionName}`);
        const section = createSection(sectionName);
        container.appendChild(section);
    });
    
    console.log('✅ Sections rendering completed');
}

/**
 * Создает секцию метрик
 */
function createSection(sectionName) {
    const normId = normalizeId(sectionName);
    const section = document.createElement('div');
    section.className = 'section';
    section.id = `section-${normId}`;

    // Заголовок секции
    const header = document.createElement('div');
    header.className = 'section-header';
    header.addEventListener('click', () => toggleSection(sectionName));

    const title = document.createElement('h3');
    title.className = 'section-title';
    title.textContent = sectionName;

    const toggle = document.createElement('span');
    toggle.className = 'section-toggle';
    toggle.textContent = '▼';

    header.appendChild(title);
    header.appendChild(toggle);
    section.appendChild(header);

    // --- ВАЖНО: создаем контейнер для метрик ---
    const content = document.createElement('div');
    content.className = 'section-content';
    content.id = `section-content-${normId}`;
    section.appendChild(content);

    return section;
}

/**
 * Переключает сворачивание/разворачивание секции
 */
function toggleSection(sectionName) {
    const normId = normalizeId(sectionName);
    const section = document.getElementById(`section-${normId}`);
    if (section) {
        section.classList.toggle('collapsed');
    }
}





/**
 * Создает карточку метрики
 */
function createMetricCard(metricId, data, error) {
    const card = document.createElement('div');
    card.className = 'metric-card';
    card.id = `metric-${metricId}`;

    // Заголовок карточки
    const header = document.createElement('div');
    header.className = 'metric-header';
    
    const title = document.createElement('h4');
    title.className = 'metric-title';
    title.textContent = data?.config?.label || metricId;
    
    const status = document.createElement('span');
    status.className = 'metric-status';
    
    if (error) {
        status.textContent = '❌';
        status.title = 'Ошибка загрузки';
    } else if (data?.config) {
        const statusInfo = getMetricStatus(data.config, data.history);
        status.textContent = statusInfo.icon;
        status.title = statusInfo.message;
        status.className = `metric-status status-${statusInfo.level}`;
    } else {
        status.textContent = '⚠️';
        status.title = 'Нет данных';
    }
    
    header.appendChild(title);
    header.appendChild(status);
    card.appendChild(header);

    // Основное содержимое
    const content = document.createElement('div');
    content.className = 'metric-content';

    if (error) {
        content.innerHTML = `<div class="metric-error">Ошибка: ${error}</div>`;
    } else if (data?.history) {
        const currentValue = getCurrentValue(data.history);
        console.log(`📊 Creating card for ${metricId}: currentValue=${currentValue}, config=`, data.config);
        
        if (currentValue !== null) {
            const formattedValue = formatValue(currentValue, data.config.format || 'fixed2');
            const unit = data.config.unit || '';
            
            const valueDisplay = document.createElement('div');
            valueDisplay.className = 'metric-value';
            valueDisplay.innerHTML = `
                <span class="value-number">${formattedValue}</span>
                ${unit ? `<span class="value-unit">${unit}</span>` : ''}
            `;
            content.appendChild(valueDisplay);
            
            console.log(`✅ Value displayed for ${metricId}: ${formattedValue} ${unit}`);
        } else {
            const noDataDisplay = document.createElement('div');
            noDataDisplay.className = 'metric-no-data';
            noDataDisplay.textContent = 'Нет данных';
            content.appendChild(noDataDisplay);
            console.warn(`⚠️ No current value for ${metricId}`);
        }

        // Контейнеры для графиков - только trend
        if (data.config.type.includes('trend')) {
            const trendContainer = document.createElement('div');
            trendContainer.id = `trend-${metricId}`;
            trendContainer.className = 'metric-chart';
            content.appendChild(trendContainer);
        }
    } else {
        const noDataDisplay = document.createElement('div');
        noDataDisplay.className = 'metric-no-data';
        noDataDisplay.textContent = 'Нет данных';
        content.appendChild(noDataDisplay);
        console.warn(`⚠️ No data for ${metricId}`);
    }

    card.appendChild(content);
    return card;
}

/**
 * Обновляет существующую карточку метрики без её пересоздания.
 * Позволяет обновлять значение и графики в реальном времени без мерцания.
 */
function updateMetricCard(metricId, data) {
    const card = document.getElementById(`metric-${metricId}`);
    if (!card) {
        console.warn(`⚠️ Card not found for update: ${metricId}`);
        return;
    }

    console.log(`🔄 Updating card for ${metricId}:`, data);

    // Обновляем статус
    const status = card.querySelector('.metric-status');
    if (status && data?.config) {
        const statusInfo = getMetricStatus(data.config, data.history);
        status.textContent = statusInfo.icon;
        status.title = statusInfo.message;
        status.className = `metric-status status-${statusInfo.level}`;
    }

    // Обновляем значение
    if (data?.history) {
        const currentValue = getCurrentValue(data.history);
        console.log(`📊 Updating value for ${metricId}: currentValue=${currentValue}`);
        
        const content = card.querySelector('.metric-content');
        if (content) {
            if (currentValue !== null) {
                const formattedValue = formatValue(currentValue, data.config.format || 'fixed2');
                const unit = data.config.unit || '';
                
                // Обновляем или создаем отображение значения
                let valueDisplay = content.querySelector('.metric-value');
                if (!valueDisplay) {
                    valueDisplay = document.createElement('div');
                    valueDisplay.className = 'metric-value';
                    content.insertBefore(valueDisplay, content.firstChild);
                }
                
                valueDisplay.innerHTML = `
                    <span class="value-number">${formattedValue}</span>
                    ${unit ? `<span class="value-unit">${unit}</span>` : ''}
                `;
                
                console.log(`✅ Value updated for ${metricId}: ${formattedValue} ${unit}`);
            } else {
                // Показываем "Нет данных"
                let noDataDisplay = content.querySelector('.metric-no-data');
                if (!noDataDisplay) {
                    noDataDisplay = document.createElement('div');
                    noDataDisplay.className = 'metric-no-data';
                    noDataDisplay.textContent = 'Нет данных';
                    content.insertBefore(noDataDisplay, content.firstChild);
                }
                
                // Удаляем старое отображение значения
                const oldValueDisplay = content.querySelector('.metric-value');
                if (oldValueDisplay) {
                    oldValueDisplay.remove();
                }
            }

            // Обновляем графики - только trend
            if (data.history?.result?.[0]?.values) {
                const values = data.history.result[0].values;
                
                if (data.config.type.includes('trend')) {
                    const trendContainer = document.getElementById(`trend-${metricId}`);
                    if (trendContainer) {
                        renderTrendChart(data.config, values, `trend-${metricId}`);
                    }
                }
            }
        }
    }
}

/**
 * Определяет статус метрики
 */
function getMetricStatus(config, history) {
    const currentValue = getCurrentValue(history);
    
    if (currentValue === null || currentValue === undefined) {
        return { status: 'unknown', color: '#6c757d' };
    }
    
    const thresholds = config.thresholds;
    if (!thresholds) {
        return { status: 'ok', color: '#28a745' };
    }
    
    if (thresholds.critical && currentValue >= thresholds.critical) {
        return { status: 'critical', color: '#dc3545' };
    }
    
    if (thresholds.warning && currentValue >= thresholds.warning) {
        return { status: 'warning', color: '#ffc107' };
    }
    
    return { status: 'ok', color: '#28a745' };
}

/**
 * Получает текущее значение из истории
 */
function getCurrentValue(history) {
    if (!history || !history.result || history.result.length === 0) {
        console.warn('⚠️ No history data for current value calculation');
        return null;
    }
    
    const result = history.result[0];
    if (!result || !result.values || result.values.length === 0) {
        console.warn('⚠️ No values in history result');
        return null;
    }
    
    // Берем последнее значение из истории
    const lastValue = result.values[result.values.length - 1];
    if (!lastValue || lastValue.length < 2) {
        console.warn('⚠️ Invalid last value format:', lastValue);
        return null;
    }
    
    const value = lastValue[1];
    console.log(`📊 Current value extracted: ${value} (type: ${typeof value})`);
    
    // Преобразуем в число, если это строка
    if (typeof value === 'string') {
        const parsed = parseFloat(value);
        if (isNaN(parsed)) {
            console.warn(`⚠️ Could not parse string value: ${value}`);
            return null;
        }
        return parsed;
    }
    
    return value;
}

/**
 * Форматирует значение метрики
 */
function formatValue(value, format) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N/A';
    }

    try {
        switch (format) {
            case 'fixed0':
                return value.toFixed(0);
            case 'fixed1':
                return value.toFixed(1);
            case 'fixed2':
                return value.toFixed(2);
            case 'fixed3':
                return value.toFixed(3);
            case 'percent':
                return Math.round(value * 100) + '%';
            case 'mb':
                const mbValue = value / 1024 / 1024;
                return mbValue.toFixed(1) + ' МБ';
            case 'kb':
                const kbValue = value / 1024;
                return kbValue.toFixed(1) + ' КБ';
            case 'bytes':
                if (value < 1024) return value.toFixed(0) + ' Б';
                if (value < 1024 * 1024) return (value / 1024).toFixed(1) + ' КБ';
                if (value < 1024 * 1024 * 1024) return (value / 1024 / 1024).toFixed(1) + ' МБ';
                return (value / 1024 / 1024 / 1024).toFixed(1) + ' ГБ';
            default:
                return value.toString();
        }
    } catch (error) {
        console.error('Error formatting value:', value, format, error);
        return value.toString();
    }
}

/**
 * Рендерит линейный график (trend)
 */
function renderTrendChart(config, values, containerId) {
    if (!values || values.length === 0) {
        console.warn(`⚠️ No data for trend chart: ${containerId}`);
        return;
    }

    try {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`⚠️ Container not found: ${containerId}`);
            return;
        }

        // Подготавливаем данные
        const timestamps = values.map(v => v[0]);
        const dataValues = values.map(v => v[1]);
        
        // Проверяем, есть ли валидные данные
        const validValues = dataValues.filter(v => v !== null && v !== undefined && !isNaN(v));
        if (validValues.length === 0) {
            console.warn(`⚠️ No valid data for trend chart: ${containerId}`);
            return;
        }

        // Вычисляем диапазон для лучшего масштабирования
        const minValue = Math.min(...validValues);
        const maxValue = Math.max(...validValues);
        const range = maxValue - minValue;
        
        // Если все значения одинаковые, добавляем небольшой диапазон
        let yMin = minValue;
        let yMax = maxValue;
        if (range === 0) {
            yMin = minValue - Math.abs(minValue) * 0.1;
            yMax = maxValue + Math.abs(maxValue) * 0.1;
        } else {
            // Добавляем 10% отступа для лучшей видимости
            const padding = range * 0.1;
            yMin = minValue - padding;
            yMax = maxValue + padding;
        }

        // Форматируем временные метки
        const timeLabels = timestamps.map(ts => {
            const date = new Date(ts * 1000);
            return date.toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
            });
        });

        const trace = {
            x: timeLabels,
            y: dataValues,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: config.color || '#3498db', width: 2 },
            marker: { 
                color: config.color || '#3498db', 
                size: 4,
                opacity: 0.7 
            },
            name: config.label || containerId
        };

        const layout = {
            margin: { t: 20, b: 40, l: 50, r: 20 },
            height: 250,
            xaxis: { 
                title: 'Время',
                tickangle: -45,
                tickmode: 'auto',
                nticks: Math.min(10, timeLabels.length)
            },
            yaxis: { 
                title: config.unit || 'Значение',
                range: [yMin, yMax]
            },
            showlegend: false
        };

        Plotly.newPlot(containerId, [trace], layout);
        console.log(`✅ Trend chart rendered for ${containerId}: ${validValues.length} points, range [${minValue.toFixed(3)}, ${maxValue.toFixed(3)}]`);

    } catch (error) {
        console.error(`❌ Failed to render trend chart for ${containerId}:`, error);
    }
}

/**
 * Экспортирует отчёт
 */
async function exportReport() {
    if (isExporting) return;
    
    try {
        isExporting = true;
        const exportBtn = document.getElementById('export-report');
        if (exportBtn) {
            exportBtn.disabled = true;
            exportBtn.textContent = '📤 Экспорт...';
        }
        
        // Создаем HTML-отчёт
        const reportHtml = await generateReportHtml();
        
        // Создаем Blob и скачиваем
        const blob = new Blob([reportHtml], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `amity-metrics-report-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Export failed:', error);
        showError('Ошибка экспорта: ' + error.message);
    } finally {
        isExporting = false;
        const exportBtn = document.getElementById('export-report');
        if (exportBtn) {
            exportBtn.disabled = false;
            exportBtn.textContent = '📤 Экспорт отчёта';
        }
    }
}

/**
 * Генерирует HTML-отчёт
 */
async function generateReportHtml() {
    const now = new Date().toLocaleString('ru-RU');
    
    let sectionsHtml = '';
    
    // Собираем данные для всех секций
    for (const sectionName of Object.keys(sectionsConfig)) {
        const sectionMetrics = sectionsConfig[sectionName] || [];
        let metricsHtml = '';
        
        for (const metricId of sectionMetrics) {
            if (allMetrics[metricId]) {
                const config = allMetrics[metricId];
                metricsHtml += `
                    <div style="margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; border-radius: 6px;">
                        <h4 style="color: #495057; margin-bottom: 10px;">${config.label}</h4>
                        <div style="display: flex; gap: 15px;">
                            ${config.type.includes('trend') ? `
                                <div style="flex: 2;">
                                    <h5>Временной ряд</h5>
                                    <div id="trend-${metricId}-export" style="height: 250px;"></div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }
        }
        
        if (metricsHtml) {
            sectionsHtml += `
                <div style="margin-bottom: 30px;">
                    <h3 style="color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 10px;">${sectionName}</h3>
                    ${metricsHtml}
                </div>
            `;
        }
    }
    
    return `
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Amity Metrics Report - ${now}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .content { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h1 { color: #495057; margin: 0; }
                h3 { color: #495057; margin: 0 0 15px 0; }
                h4 { color: #495057; margin: 0 0 10px 0; }
                h5 { color: #6c757d; margin: 0 0 8px 0; }
                .debug-info {
                    margin-top: 20px;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    font-size: 0.9em;
                    overflow-y: auto;
                    max-height: 200px; /* Ограничиваем высоту */
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Отчёт метрик Amity</h1>
                <p>Сгенерирован: ${now}</p>
                <p>Интервал: ${currentInterval} минут</p>
            </div>
            <div class="content">
                ${sectionsHtml}
            </div>
            <script>
                // Данные для графиков будут загружены здесь
                const sectionsConfig = ${JSON.stringify(sectionsConfig)};
                const allMetrics = ${JSON.stringify(allMetrics)};
                const currentInterval = ${currentInterval};
                
                // Функция для загрузки и отображения графиков
                async function loadAndRenderCharts() {
                    for (const sectionName of Object.keys(sectionsConfig)) {
                        const sectionMetrics = sectionsConfig[sectionName] || [];
                        
                        for (const metricId of sectionMetrics) {
                            if (allMetrics[metricId]) {
                                const config = allMetrics[metricId];
                                
                                try {
                                    // Загружаем данные
                                    const response = await fetch('/api/metrics/' + metricId + '/history?interval=' + currentInterval);
                                    const data = await response.json();
                                    
                                    if (data.data && data.data.result && data.data.result.length > 0) {
                                        const result = data.data.result[0];
                                        
                                        if (result.values && result.values.length > 0) {
                                            const timestamps = result.values.map(([ts, _]) => new Date(ts * 1000));
                                            const values = result.values.map(([_, v]) => v);
                                            
                                            // Рендерим графики - только trend
                                            if (config.type.includes('trend')) {
                                                const trendData = [{
                                                    x: timestamps,
                                                    y: values,
                                                    type: 'scatter',
                                                    mode: 'lines',
                                                    line: { color: config.color, width: 2 },
                                                    fill: 'tonexty',
                                                    fillcolor: config.color + '20'
                                                }];
                                                
                                                const trendLayout = {
                                                    margin: { t: 20, b: 40, l: 50, r: 20 },
                                                    height: 250,
                                                    xaxis: { title: 'Время' },
                                                    yaxis: { title: config.unit || 'Значение' }
                                                };
                                                
                                                Plotly.newPlot('trend-' + metricId + '-export', trendData, trendLayout);
                                            }
                                        }
                                    }
                                } catch (error) {
                                    console.error('Failed to load chart for ' + metricId + ':', error);
                                }
                            }
                        }
                    }
                }
                
                // Запускаем загрузку графиков
                loadAndRenderCharts();
            </script>
        </body>
        </html>
    `;
}

/**
 * Запускает автообновление
 */
function startAutoUpdate() {
    // Интервал автообновления в миллисекундах. Обновляем каждую секунду для realtime‑режима,
    // обновляя существующие карточки без перерисовки страницы.
    const AUTO_UPDATE_INTERVAL_MS = 1000;

    if (updateTimer) {
        clearInterval(updateTimer);
    }

    updateTimer = setInterval(async () => {
        await loadSectionsData();
    }, AUTO_UPDATE_INTERVAL_MS);
}

/**
 * Показывает индикатор загрузки
 */
function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'block';
    }
}

/**
 * Скрывает индикатор загрузки
 */
function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

/**
 * Показывает ошибку
 */
function showError(message) {
    const errorDiv = document.getElementById('error');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

/**
 * Обновляет статус
 */
function updateStatus(status) {
    const indicator = document.getElementById('status-indicator');
    if (indicator) {
        indicator.className = `status-indicator status-${status}`;
    }
    
    const lastUpdated = document.getElementById('last-updated');
    if (lastUpdated) {
        lastUpdated.textContent = new Date().toLocaleString('ru-RU');
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', initDashboard);
