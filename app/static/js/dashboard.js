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

/**
 * Инициализация дашборда
 */
async function initDashboard() {
    try {
        // Проверяем debug-режим из URL
        const urlParams = new URLSearchParams(window.location.search);
        debugMode = urlParams.get('debug') === 'true';
        
        // Загружаем конфигурацию секций
        await loadSectionsConfig();
        
        // Инициализируем интерфейс
        initControls();
        
        // Загружаем данные
        await loadSectionsData();
        
        // Запускаем автообновление
        startAutoUpdate();
        
        // Скрываем индикатор загрузки
        hideLoading();
        
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
        showError('Ошибка инициализации дашборда: ' + error.message);
    }
}

/**
 * Загружает конфигурацию секций и метрик
 */
async function loadSectionsConfig() {
    try {
        const response = await fetch('/api/sections');
        const data = await response.json();
        
        sectionsConfig = data.sections || {};
        allMetrics = data.all_metrics || {};
        timeIntervals = data.time_intervals || [];
        
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
        }
        
    } catch (error) {
        console.error('Failed to load sections config:', error);
        throw new Error('Не удалось загрузить конфигурацию секций');
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
    try {

 const container = document.getElementById('sections-container');
const isFirst = firstLoad && container && !container.hasChildNodes();
    if (isFirst) {
    showLoading();
    updateStatus('loading');
    renderSections();
} 
        
        // Загружаем данные для каждой секции
        const sectionPromises = Object.keys(sectionsConfig).map(async (sectionName) => {
            await loadSectionData(sectionName);
        });
        
        await Promise.all(sectionPromises);
        
        updateStatus('ok');
        
    } catch (error) {
        console.error('Failed to load sections data:', error);
        showError('Ошибка загрузки данных: ' + error.message);
        updateStatus('error');
    } finally {
      if (firstLoad) {
            hideLoading();
            firstLoad = false;
        }
    }
}

/**
 * Рендерит секции на странице
 */
function renderSections() {
    const container = document.getElementById('sections-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Сортируем секции: KPI всегда первая
    const sectionNames = Object.keys(sectionsConfig);
    sectionNames.sort((a, b) => {
        if (a === 'KPI') return -1;
        if (b === 'KPI') return 1;
        return 0;
    });
    sectionNames.forEach(sectionName => {
        const section = createSection(sectionName);
        container.appendChild(section);
    });
}

/**
 * Создает секцию метрик
 */
function createSection(sectionName) {
    const section = document.createElement('div');
    section.className = 'section';
    section.id = `section-${sectionName}`;
    
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
    
    // Контент секции
    const content = document.createElement('div');
    content.className = 'section-content';
    content.id = `section-content-${sectionName}`;
    
    // Добавляем индикатор загрузки
    const loading = document.createElement('div');
    loading.className = 'loading-indicator';
    loading.innerHTML = '<div class="spinner"></div> Загрузка метрик...';
    content.appendChild(loading);
    
    section.appendChild(header);
    section.appendChild(content);
    
    return section;
}

/**
 * Переключает сворачивание/разворачивание секции
 */
function toggleSection(sectionName) {
    const section = document.getElementById(`section-${sectionName}`);
    if (section) {
        section.classList.toggle('collapsed');
    }
}

/**
 * Загружает данные для конкретной секции
 */
async function loadSectionData(sectionName) {
    try {
        const sectionMetrics = sectionsConfig[sectionName] || [];
        const content = document.getElementById(`section-content-${sectionName}`);
        
        if (!content) return;
        
        // Если в секции нет метрик — показываем stub и выходим
        if (sectionMetrics.length === 0) {
            // Если ещё нет содержимого, создаём сообщение
            if (!content.hasChildNodes()) {
                content.innerHTML = '<div class="no-data">Нет метрик в этой секции</div>';
            }
            return;
        }
        
        // Загружаем данные для каждой метрики
        const metricPromises = sectionMetrics.map(async (metricId) => {
            try {
                const metricData = await loadMetricData(metricId);
                return { id: metricId, data: metricData };
            } catch (error) {
                console.error(`Failed to load metric ${metricId}:`, error);
                return { id: metricId, data: null, error: error.message };
            }
        });
        
        const results = await Promise.all(metricPromises);

        results.forEach(result => {
            const existingCard = document.getElementById(`metric-${result.id}`);
            if (existingCard) {
                // Если карточка уже существует, обновляем её
                if (result.data) {
                    updateMetricCard(result.id, result.data);
                } else if (result.error) {
                    existingCard.innerHTML = `<div class="metric-header"><h4 class="metric-title">${result.id}</h4></div><div class="metric-error">Ошибка: ${result.error}</div>`;
                }
            } else {
                // Если карточки нет, создаём новую и добавляем
                const metricCard = createMetricCard(result.id, result.data, result.error);
                content.appendChild(metricCard);
                // Отрисовываем графики после добавления новой карточки
                if (result.data && result.data.history && result.data.history.result && result.data.history.result.length > 0) {
                    const config = result.data.config;
                    const history = result.data.history;
                    const metricId = result.id;
                    const resultObj = history.result[0];
                    if (resultObj.values && resultObj.values.length > 0) {
                        if (config.type.includes('trend')) {
                            renderTrendChart(config, resultObj.values, `trend-${metricId}`);
                        }
                        if (config.type.includes('bar')) {
                            renderBarChart(config, resultObj.values, `bar-${metricId}`);
                        }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error(`Failed to load section ${sectionName}:`, error);
        const content = document.getElementById(`section-content-${sectionName}`);
        if (content) {
            content.innerHTML = `<div class="metric-error">Ошибка загрузки секции: ${error.message}</div>`;
        }
    }
}

/**
 * Загружает данные для конкретной метрики
 */
async function loadMetricData(metricId) {
    if (!allMetrics[metricId]) {
        throw new Error(`Метрика '${metricId}' не найдена в конфигурации`);
    }
    
    const metricConfig = allMetrics[metricId];
    
    // Загружаем историю метрики
    const params = new URLSearchParams({
        interval: currentInterval.toString()
    });
    
    const response = await fetch(`/api/metrics/${metricId}/history?${params}`);
    const data = await response.json();
    
    if (data.status === 'error') {
        throw new Error(data.error || 'Unknown error');
    }
    
    return {
        config: metricConfig,
        history: data.data || {},
        debug: debugMode ? data : null
    };
}

/**
 * Создает карточку метрики
 */
function createMetricCard(metricId, data, error) {
    const card = document.createElement('div');
    card.className = 'metric-card';
    card.id = `metric-${metricId}`;
    
    if (error) {
        card.innerHTML = `
            <div class="metric-header">
                <h4 class="metric-title">${metricId}</h4>
            </div>
            <div class="metric-error">Ошибка: ${error}</div>
        `;
        return card;
    }
    
    if (!data || !data.config) {
        card.innerHTML = `
            <div class="metric-header">
                <h4 class="metric-title">${metricId}</h4>
            </div>
            <div class="metric-error">Нет данных</div>
        `;
        return card;
    }
    
    const config = data.config;
    const history = data.history;
    const debug = data.debug;
    
    // Проверка на отсутствие данных
    if (!history || !history.result || history.result.length === 0 || !history.result[0].values || history.result[0].values.length === 0) {
        card.innerHTML = `
            <div class="metric-header">
                <h4 class="metric-title">${config.label || metricId}</h4>
            </div>
            <div class="metric-error">Нет данных за выбранный период</div>
        `;
        return card;
    }
    
    // Определяем статус
    const status = getMetricStatus(config, history);
    
    // Заголовок карточки
    const header = document.createElement('div');
    header.className = 'metric-header';
    
    const title = document.createElement('h4');
    title.className = 'metric-title';
    title.textContent = config.label || metricId;
    
    const valueContainer = document.createElement('div');
    valueContainer.className = 'metric-value-container';
    
    const value = document.createElement('span');
    value.className = 'metric-value';
    value.style.color = status.color;

    // Получаем текущее значение
    const currentValue = getCurrentValue(history);
    if (currentValue !== null && currentValue !== undefined) {
        const formattedValue = formatValue(currentValue, config.format);
        value.textContent = formattedValue;
    } else {
        value.textContent = 'N/A';
    }

    // Присваиваем ID, чтобы можно было обновлять значение без пересоздания карточки
    value.id = `metric-value-${metricId}`;

    const unit = document.createElement('span');
    unit.className = 'metric-unit';
    unit.textContent = config.unit || '';
    // Присваиваем ID для единицы измерения (при обновлении может измениться цвет)
    unit.id = `metric-unit-${metricId}`;
    
    valueContainer.appendChild(value);
    valueContainer.appendChild(unit);
    
    header.appendChild(title);
    header.appendChild(valueContainer);
    
    // Контейнер для графиков
    const chartsContainer = document.createElement('div');
    chartsContainer.className = 'metric-charts';
    
    // Рендерим графики в зависимости от типа
    if (config.type.includes('trend')) {
        const trendChart = document.createElement('div');
        trendChart.className = 'metric-trend-chart';
        trendChart.id = `trend-${metricId}`;
        chartsContainer.appendChild(trendChart);
    }
    
    if (config.type.includes('bar')) {
        const barChart = document.createElement('div');
        barChart.className = 'metric-bar-chart';
        barChart.id = `bar-${metricId}`;
        chartsContainer.appendChild(barChart);
    }
    
    card.appendChild(header);
    card.appendChild(chartsContainer);
    
    // Рендерим графики (Plotly) всегда, если есть данные
    if (history && history.result && history.result.length > 0) {
        const result = history.result[0];
        if (result.values && result.values.length > 0) {
            if (config.type.includes('trend')) {
                renderTrendChart(config, result.values, `trend-${metricId}`);
            }
            if (config.type.includes('bar')) {
                renderBarChart(config, result.values, `bar-${metricId}`);
            }
        }
    }
    
    // Debug-информация (убрано по просьбе пользователя)
    // if (debugMode && debug) {
    //     const debugInfo = document.createElement('div');
    //     debugInfo.className = 'debug-info';
    //     const historyData = debug.data?.result?.[0]?.values || [];
    //     const values = historyData.map(([_, v]) => v).filter(v => v !== null && v !== undefined);
    //     const min = values.length > 0 ? Math.min(...values) : 'N/A';
    //     const max = values.length > 0 ? Math.max(...values) : 'N/A';
    //     const count = values.length;
    //     debugInfo.innerHTML = `
    //         <strong>Debug Info:</strong><br>
    //         <pre>JSON: ${JSON.stringify(debug, null, 2)}</pre>
    //         <strong>Stats:</strong> min: ${min}, max: ${max}, count: ${count}
    //     `;
    //     card.appendChild(debugInfo);
    // }
    
    return card;
}

/**
 * Обновляет существующую карточку метрики без её пересоздания.
 * Позволяет обновлять значение и графики в реальном времени без мерцания.
 */
function updateMetricCard(metricId, data) {
    const card = document.getElementById(`metric-${metricId}`);
    if (!card || !data || !data.config || !data.history) {
        return;
    }
    const config = data.config;
    const history = data.history;

    // Обновляем значение
    const valueEl = document.getElementById(`metric-value-${metricId}`);
    if (valueEl) {
        const currentValue = getCurrentValue(history);
        if (currentValue !== null && currentValue !== undefined) {
            const formatted = formatValue(currentValue, config.format);
            valueEl.textContent = formatted;
        } else {
            valueEl.textContent = 'N/A';
        }
        // Обновляем цвет статуса
        const status = getMetricStatus(config, history);
        valueEl.style.color = status.color;
    }

    // Обновляем графики, если есть данные
    if (history && history.result && history.result.length > 0) {
        const resultObj = history.result[0];
        if (resultObj.values && resultObj.values.length > 0) {
            if (config.type.includes('trend')) {
                renderTrendChart(config, resultObj.values, `trend-${metricId}`);
            }
            if (config.type.includes('bar')) {
                renderBarChart(config, resultObj.values, `bar-${metricId}`);
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
        return null;
    }
    
    const result = history.result[0];
    if (!result.values || result.values.length === 0) {
        return null;
    }
    
    const lastPoint = result.values[result.values.length - 1];
    // Значение приходит строкой из API, конвертируем в число
    const val = lastPoint[1];
    if (val === null || val === undefined) {
        return null;
    }
    const parsed = typeof val === 'string' ? parseFloat(val) : val;
    return isNaN(parsed) ? null : parsed;
}

/**
 * Форматирует значение метрики
 */
function formatValue(value, format) {
    // Если значение пустое – показываем N/A
    if (value === null || value === undefined) {
        return 'N/A';
    }
    // Приводим строковые значения к числам, иначе методы toFixed недоступны
    let num = value;
    if (typeof num === 'string') {
        // пустая строка или непреобразуемое значение → N/A
        const parsed = parseFloat(num);
        if (!isNaN(parsed)) {
            num = parsed;
        }
    }
    const formatter = formatFunctions[format] || formatFunctions.fixed2;
    return formatter(num);
}

/**
 * Рендерит линейный график (trend)
 */
function renderTrendChart(config, values, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !values || values.length === 0) {
        return;
    }
    
    const timestamps = values.map(([ts, _]) => new Date(ts * 1000));
    // Приводим значения к числам, т.к. API возвращает строки
    const dataValues = values.map(([_, v]) => {
        const parsed = typeof v === 'string' ? parseFloat(v) : v;
        return isNaN(parsed) ? null : parsed;
    });
    
    const data = [{
        x: timestamps,
        y: dataValues,
        type: 'scatter',
        mode: 'lines',
        line: {
            color: config.color,
            width: 2
        },
        fill: 'tonexty',
        fillcolor: config.color + '20',
        hovertemplate: '%{y:.3f}<extra></extra>'
    }];
    
    const layout = {
        margin: { t: 10, b: 30, l: 40, r: 10 },
        height: 150,
        xaxis: {
            showgrid: false,
            tickformat: '%H:%M',
            tickangle: 0,
            tickfont: { size: 12 }
        },
        yaxis: {
            showgrid: true,
            zeroline: false,
            tickfont: { size: 12 },
            title: config.unit,
            titlefont: { size: 12 }
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        hovermode: 'x unified',
        hoverlabel: {
            bgcolor: 'rgba(0,0,0,0.8)',
            font: { size: 11 }
        }
    };
    
    Plotly.react(container, data, layout, {
        displayModeBar: false,
        responsive: true
    });
}

/**
 * Рендерит гистограмму (bar)
 */
function renderBarChart(config, values, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !values || values.length === 0) {
        return;
    }
    
    // Приводим строки к числам и отбрасываем нечисловые значения
    const dataValues = values
        .map(([_, v]) => {
            const parsed = typeof v === 'string' ? parseFloat(v) : v;
            return isNaN(parsed) ? null : parsed;
        })
        .filter(v => v !== null && v !== undefined);
    
    if (dataValues.length === 0) {
        return;
    }
    
    const data = [{
        x: dataValues,
        type: 'histogram',
        nbinsx: 10,
        marker: {
            color: config.color,
            opacity: 0.7
        },
        hovertemplate: 'Количество: %{y}<br>Значение: %{x:.3f}<extra></extra>'
    }];
    
    const layout = {
        margin: { t: 10, b: 30, l: 40, r: 10 },
        height: 150,
        xaxis: {
            showgrid: false,
            tickfont: { size: 12 },
            title: config.unit,
            titlefont: { size: 12 }
        },
        yaxis: {
            showgrid: true,
            zeroline: false,
            tickfont: { size: 12 },
            title: 'Количество',
            titlefont: { size: 12 }
        },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        hovermode: 'closest',
        hoverlabel: {
            bgcolor: 'rgba(0,0,0,0.8)',
            font: { size: 11 }
        }
    };
    
    Plotly.react(container, data, layout, {
        displayModeBar: false,
        responsive: true
    });
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
                            ${config.type.includes('bar') ? `
                                <div style="flex: 1;">
                                    <h5>Распределение</h5>
                                    <div id="bar-${metricId}-export" style="height: 250px;"></div>
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
                                            
                                            // Рендерим графики
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
                                            
                                            if (config.type.includes('bar')) {
                                                const barData = [{
                                                    x: values,
                                                    type: 'histogram',
                                                    nbinsx: 10,
                                                    marker: { color: config.color, opacity: 0.7 }
                                                }];
                                                
                                                const barLayout = {
                                                    margin: { t: 20, b: 40, l: 50, r: 20 },
                                                    height: 250,
                                                    xaxis: { title: config.unit || 'Значение' },
                                                    yaxis: { title: 'Количество' }
                                                };
                                                
                                                Plotly.newPlot('bar-' + metricId + '-export', barData, barLayout);
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
