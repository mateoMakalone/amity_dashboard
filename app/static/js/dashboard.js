/**
 * Форматирование чисел
 */
const formatFunctions = {
    fixed0: x => x.toFixed(0),
    fixed2: x => x.toFixed(2),
    fixed3: x => x.toFixed(3),
    roundFormat: x => Math.round(x).toLocaleString()
};

/**
 * Преобразует snake_case/underscore_case в Title Case
 * @param {string} str
 * @returns {string}
 */
function toTitleCase(str) {
    return str
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Интервал обновления (мс)
 */
const UPDATE_INTERVAL = 1000;

/**
 * Показывает или скрывает спиннер загрузки
 * @param {boolean} show
 */
function toggleSpinner(show) {
    const spinner = document.getElementById('spinner');
    if (spinner) spinner.style.display = show ? 'block' : 'none';
}

// Глобальные переменные для управления polling'ом истории
let historyPollingStarted = false;
let historyFetching = false;
let currentHistoryData = {};

/**
 * Безопасное получение истории метрик с защитой от перегрузки
 * @returns {Promise<object>} данные истории
 */
async function fetchHistory() {
    if (historyFetching) {
        // Если запрос уже идет, возвращаем последние данные
        return currentHistoryData;
    }
    
    historyFetching = true;
    
    try {
        const resp = await fetch('/history');
        const data = await resp.json();
        currentHistoryData = data;
        return data;
    } catch (err) {
        console.error('Error fetching history:', err);
        return currentHistoryData; // Возвращаем последние данные при ошибке
    } finally {
        historyFetching = false;
    }
}

/**
 * Запускает polling истории метрик (только один раз)
 */
function startHistoryPolling() {
    if (historyPollingStarted) return;
    historyPollingStarted = true;
    
    // Начальный вызов
    fetchHistory();
    
    // Устанавливаем интервал для обновления истории
    setInterval(fetchHistory, 1000);
}

/**
 * Обновляет графики истории без пересоздания DOM
 * @param {object} historyData - данные истории
 * @param {string} metricName - имя метрики
 * @param {HTMLElement} plotDiv - элемент для графика
 * @param {string} color - цвет линии
 */
function updateHistoryPlot(historyData, metricName, plotDiv, color = '#800000') {
    if (!historyData[metricName] || !plotDiv) return;
    
    const x = historyData[metricName].map(([ts, _]) => new Date(ts * 1000));
    const y = historyData[metricName].map(([_, v]) => v);
    
    Plotly.react(plotDiv, [{
        x, 
        y, 
        type: 'scatter', 
        mode: 'lines', 
        line: {color: color}
    }], {
        margin: {t: 10, b: 30, l: 40, r: 10},
        height: 120,
        xaxis: {showgrid: false, tickformat: '%H:%M:%S'},
        yaxis: {showgrid: true, zeroline: false},
        displayModeBar: false
    }, {displayModeBar: false});
}

// Пороговые значения для KPI-метрик (из ТЗ)
const KPI_THRESHOLDS = {
    tx_pool_size: { warning: 1000, critical: 5000 },
    jetty_server_requests_seconds_avg: { warning: 1.0, critical: 2.0 },
    process_cpu_usage: { warning: 0.85, critical: 0.95 },
    postgres_locks: { warning: 10, critical: 50 },
    jvm_gc_pause_seconds_sum: { warning: 1.0, critical: 3.0 },
    postgres_connections: { warning: 100, critical: 150 },
    jvm_memory_used_bytes: { warning: 0.75, critical: 0.9, isRatio: true },
    system_load_average_1m: { warning: 2.0, critical: 4.0 },
};

/**
 * Находит значение метрики с поддержкой лейблов
 * @param {string} base - базовое имя метрики
 * @param {object} metrics - объект с метриками
 * @returns {number} значение метрики или 0.0
 */
function findMetricValue(base, metrics) {
    if (metrics[base] !== undefined) return metrics[base];
    const match = Object.keys(metrics).find(k => k.startsWith(base + '{'));
    return match ? metrics[match] : 0.0;
}

function getKpiColor(metric, value, data) {
    const t = KPI_THRESHOLDS[metric];
    if (!t) return '';
    let v = value;
    if (t.isRatio) {
        // Для heap: jvm_memory_used_bytes / jvm_memory_max_bytes
        const used = findMetricValue('jvm_memory_used_bytes', data.metrics);
        const max = findMetricValue('jvm_memory_max_bytes', data.metrics);
        if (used !== undefined && max && max > 0) {
            v = used / max;
        } else {
            return '';
        }
    }
    if (v < t.warning) return 'kpi-green';
    if (v <= t.critical) return 'kpi-yellow';
    return 'kpi-red';
}

// Глобальный тултип для предотвращения зависаний
let globalTooltip = null;
let tooltipTimeout = null;

/**
 * Создает info-icon с надежным тултипом
 * @param {string} tooltipText - текст тултипа
 * @returns {HTMLElement} info-icon элемент
 */
function createInfoIcon(tooltipText) {
    const icon = document.createElement('span');
    icon.className = 'info-icon';
    icon.tabIndex = 0;
    icon.innerHTML = '&#9432;';
    
    icon.addEventListener('mouseenter', function(e) {
        // Очищаем предыдущий таймаут
        if (tooltipTimeout) {
            clearTimeout(tooltipTimeout);
            tooltipTimeout = null;
        }
        
        // Удаляем предыдущий тултип
        if (globalTooltip) {
            document.body.removeChild(globalTooltip);
            globalTooltip = null;
        }
        
        // Создаем новый тултип
        globalTooltip = document.createElement('div');
        globalTooltip.className = 'custom-tooltip';
        globalTooltip.textContent = tooltipText;
        document.body.appendChild(globalTooltip);
        
        const rect = icon.getBoundingClientRect();
        globalTooltip.style.left = (rect.right + 8) + 'px';
        globalTooltip.style.top = (rect.top - 4) + 'px';
    });
    
    icon.addEventListener('mouseleave', function() {
        // Устанавливаем таймаут для скрытия тултипа
        tooltipTimeout = setTimeout(() => {
            if (globalTooltip) {
                document.body.removeChild(globalTooltip);
                globalTooltip = null;
            }
        }, 100);
    });
    
    return icon;
}

/**
 * Обновляет KPI метрики без пересоздания DOM
 * @param {object} data - данные метрик
 */
async function updateProminentMetrics(data) {
    const container = document.getElementById('prominent-metrics');
    
    // Сохраняем позицию скролла
    const scrollY = window.scrollY;
    
    // Собираем существующие карточки
    const existingCards = {};
    container.querySelectorAll('.key-metric-card').forEach(card => {
        const metric = card.getAttribute('data-metric');
        existingCards[metric] = card;
    });
    
    const metricsToShow = Object.keys(data.prominent);
    
    // Удаляем карточки, которых больше нет
    for (const metric in existingCards) {
        if (!metricsToShow.includes(metric)) {
            container.removeChild(existingCards[metric]);
        }
    }
    
    // Обновляем или добавляем карточки
    for (const metricName of metricsToShow) {
        const config = data.prominent[metricName];
        const section = 'KPI';
        let shortTitle = (METRIC_LABELS[section] && METRIC_LABELS[section][metricName]) ? 
            METRIC_LABELS[section][metricName] : (config.title || metricName);
        
        // Используем findMetricValue для корректной привязки метрик с лейблами
        const value = findMetricValue(metricName, data.metrics);
        const formatType = config.format || "fixed2";
        const formatter = formatFunctions[formatType] || formatFunctions.fixed2;
        const formattedValue = formatter(value);
        const displayValue = `${formattedValue} ${config.unit || ""}`.trim();
        
        let card = existingCards[metricName];
        if (!card) {
            // Создаем новую карточку
            card = document.createElement('div');
            card.className = `key-metric-card card`;
            card.setAttribute('data-metric', metricName);
            
            // Название + info icon
            const nameDiv = document.createElement('div');
            nameDiv.className = 'key-metric-name metric-name';
            nameDiv.textContent = shortTitle;
            const infoIcon = createInfoIcon(getMetricTooltip(section, metricName, value !== 0.0));
            nameDiv.appendChild(infoIcon);
            nameDiv.title = '';
            card.appendChild(nameDiv);
            
            const valueDiv = document.createElement('div');
            valueDiv.className = 'key-metric-value';
            card.appendChild(valueDiv);
            
            const plotDiv = document.createElement('div');
            plotDiv.className = 'metric-history-plot';
            plotDiv.id = `plot-${metricName}`;
            card.appendChild(plotDiv);
            
            container.appendChild(card);
        }
        
        // Обновляем значение in-place
        const valueDiv = card.querySelector('.key-metric-value');
        if (valueDiv.textContent !== displayValue) {
            valueDiv.textContent = displayValue;
        }
        
        // Обновляем тултип info-icon
        const nameDiv = card.querySelector('.key-metric-name');
        if (nameDiv && nameDiv.querySelector('.info-icon')) {
            const icon = nameDiv.querySelector('.info-icon');
            // Обновляем тултип без пересоздания иконки
            icon.onmouseenter = function(e) {
                if (tooltipTimeout) {
                    clearTimeout(tooltipTimeout);
                    tooltipTimeout = null;
                }
                if (globalTooltip) {
                    document.body.removeChild(globalTooltip);
                    globalTooltip = null;
                }
                globalTooltip = document.createElement('div');
                globalTooltip.className = 'custom-tooltip';
                globalTooltip.textContent = getMetricTooltip(section, metricName, value !== 0.0);
                document.body.appendChild(globalTooltip);
                const rect = icon.getBoundingClientRect();
                globalTooltip.style.left = (rect.right + 8) + 'px';
                globalTooltip.style.top = (rect.top - 4) + 'px';
            };
            icon.onmouseleave = function() {
                tooltipTimeout = setTimeout(() => {
                    if (globalTooltip) {
                        document.body.removeChild(globalTooltip);
                        globalTooltip = null;
                    }
                }, 100);
            };
        }
        
        // Цветовая индикация для KPI
        card.classList.remove('kpi-green', 'kpi-yellow', 'kpi-red');
        const colorClass = getKpiColor(metricName, value, data);
        if (colorClass) card.classList.add(colorClass);
        
        // График - используем текущие данные истории
        const plotDiv = card.querySelector('.metric-history-plot');
        if (plotDiv) {
            updateHistoryPlot(currentHistoryData, metricName, plotDiv, '#800000');
        }
    }
    
    // Восстанавливаем позицию скролла
    window.scrollTo(0, scrollY);
}

function getCategoryConfig(category, config) {
    return config.find(c => c.category === category) || {};
}

function stripCategoryPrefix(metricName, categoryConfig) {
    if (!categoryConfig || !categoryConfig.metrics) return metricName;
    for (const pattern of categoryConfig.metrics) {
        const match = pattern.match(/^([a-zA-Z0-9]+)_/);
        if (match && metricName.startsWith(match[1] + '_')) {
            return metricName.slice(match[1].length + 1);
        }
    }
    return metricName;
}

/**
 * Обновляет секции метрик без пересоздания DOM
 * @param {object} data
 */
async function updateMetricsSections(data) {
    const container = document.getElementById('metrics-sections');
    
    // Сохраняем позицию скролла
    const scrollY = window.scrollY;
    
    // Собираем все секции и метрики, которые должны быть
    const categories = {};
    for (const categoryConfig of data.config) {
        categories[categoryConfig.category] = [];
        for (const pattern of categoryConfig.metrics) {
            let found = false;
            for (const metricName in data.metrics) {
                if (metricName === pattern) {
                    categories[categoryConfig.category].push(metricName);
                    found = true;
                    break;
                }
            }
            if (!found) {
                categories[categoryConfig.category].push(pattern);
            }
        }
    }
    
    const orderedCategories = data.config
        .sort((a, b) => a.priority - b.priority)
        .map(c => c.category);
    
    // Секции: ищем существующие, добавляем новые, удаляем лишние
    const existingSections = {};
    container.querySelectorAll('.metrics-section').forEach(sec => {
        const cat = sec.getAttribute('data-category');
        existingSections[cat] = sec;
    });
    
    // Удаляем лишние секции
    for (const cat in existingSections) {
        if (!orderedCategories.includes(cat)) {
            container.removeChild(existingSections[cat]);
        }
    }
    
    // Обновляем/добавляем секции
    for (const category of orderedCategories) {
        let section = existingSections[category];
        const categoryConfig = getCategoryConfig(category, data.config);
        const color = categoryConfig.color || '#eee';
        
        if (!section) {
            section = document.createElement('section');
            section.className = 'metrics-section';
            section.setAttribute('data-category', category);
            section.style.borderLeft = `6px solid ${color}`;
            section.innerHTML = `<h2 class="section-title">${category}</h2><div class="metrics-grid" id="section-${category}"></div>`;
            container.appendChild(section);
        } else {
            section.style.borderLeft = `6px solid ${color}`;
        }
        
        const grid = section.querySelector('.metrics-grid');
        
        // Карточки метрик: ищем существующие, добавляем новые, удаляем лишние
        const existingCards = {};
        grid.querySelectorAll('.metric-card').forEach(card => {
            const metric = card.getAttribute('data-metric');
            existingCards[metric] = card;
        });
        
        const metricsToShow = categories[category];
        
        // Удаляем лишние карточки
        for (const metric in existingCards) {
            if (!metricsToShow.includes(metric)) {
                grid.removeChild(existingCards[metric]);
            }
        }
        
        // Обновляем/добавляем карточки
        for (const name of metricsToShow) {
            const shortName = stripCategoryPrefix(name, categoryConfig);
            let card = existingCards[name];
            
            if (!card) {
                card = document.createElement('div');
                card.className = 'metric-card card';
                card.setAttribute('data-metric', name);
                
                // Название + info icon
                const nameDiv = document.createElement('div');
                nameDiv.className = 'metric-name';
                nameDiv.textContent = (METRIC_LABELS[category] && METRIC_LABELS[category][name]) ? 
                    METRIC_LABELS[category][name] : toTitleCase(shortName);
                const infoIcon = createInfoIcon(getMetricTooltip(category, name, false));
                nameDiv.appendChild(infoIcon);
                nameDiv.title = '';
                card.appendChild(nameDiv);
                
                const valueDiv = document.createElement('div');
                valueDiv.className = 'metric-value';
                card.appendChild(valueDiv);
                
                const plotDiv = document.createElement('div');
                plotDiv.className = 'metric-history-plot';
                plotDiv.id = `plot-${name}`;
                card.appendChild(plotDiv);
                
                grid.appendChild(card);
            }
            
            // Обновляем значение in-place
            const valueDiv = card.querySelector('.metric-value');
            const value = findMetricValue(name, data.metrics);
            const newValue = value.toFixed(2);
            
            if (valueDiv.textContent !== newValue) {
                valueDiv.textContent = newValue;
            }
            
            // Обновляем тултип info-icon
            const nameDiv = card.querySelector('.metric-name');
            if (nameDiv && nameDiv.querySelector('.info-icon')) {
                const icon = nameDiv.querySelector('.info-icon');
                // Обновляем тултип без пересоздания иконки
                icon.onmouseenter = function(e) {
                    if (tooltipTimeout) {
                        clearTimeout(tooltipTimeout);
                        tooltipTimeout = null;
                    }
                    if (globalTooltip) {
                        document.body.removeChild(globalTooltip);
                        globalTooltip = null;
                    }
                    globalTooltip = document.createElement('div');
                    globalTooltip.className = 'custom-tooltip';
                    globalTooltip.textContent = getMetricTooltip(category, name, value !== 0.0);
                    document.body.appendChild(globalTooltip);
                    const rect = icon.getBoundingClientRect();
                    globalTooltip.style.left = (rect.right + 8) + 'px';
                    globalTooltip.style.top = (rect.top - 4) + 'px';
                };
                icon.onmouseleave = function() {
                    tooltipTimeout = setTimeout(() => {
                        if (globalTooltip) {
                            document.body.removeChild(globalTooltip);
                            globalTooltip = null;
                        }
                    }, 100);
                };
            }
            
            // График - используем текущие данные истории
            const plotDiv = card.querySelector('.metric-history-plot');
            if (category === 'System' && plotDiv) {
                updateHistoryPlot(currentHistoryData, name, plotDiv, color);
            }
        }
    }
    
    // Восстанавливаем позицию скролла
    window.scrollTo(0, scrollY);
}

async function updateTransactionsSection(data) {
    const container = document.getElementById('metrics-sections');
    let section = container.querySelector('section[data-category="Transactions"]');
    if (!section) {
        section = document.createElement('section');
        section.className = 'metrics-section';
        section.setAttribute('data-category', 'Transactions');
        section.innerHTML = `<h2 class="section-title">Transactions</h2><div class="transactions-history-plot" id="transactions-history-plot"></div>`;
        container.prepend(section);
    }
    const plotDiv = section.querySelector('.transactions-history-plot');
    
    // Метрики для графика
    const metricsList = [
        'postgres_transactions_total{database="db01"}',
        'postgres_rows_updated_total{database="db01"}',
        'postgres_rows_deleted_total{database="db01"}'
    ];
    const colors = ['#2980b9', '#27ae60', '#e74c3c'];
    const traces = [];
    
    metricsList.forEach((metric, idx) => {
        if (currentHistoryData[metric]) {
            const x = currentHistoryData[metric].map(([ts, _]) => new Date(ts * 1000));
            const y = currentHistoryData[metric].map(([_, v]) => v);
            traces.push({
                x,
                y,
                name: METRIC_LABELS.Transactions[metric] || metric,
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: colors[idx] }
            });
        }
    });
    
    Plotly.react(plotDiv, traces, {
        margin: { t: 30, b: 30, l: 40, r: 10 },
        height: 220,
        xaxis: { showgrid: false, tickformat: '%H:%M:%S', title: 'Time' },
        yaxis: { showgrid: true, zeroline: false, title: 'Value' },
        legend: { orientation: 'h', y: -0.2 },
        title: 'Transactions History'
    }, { displayModeBar: false });
}

function getMetricCategory(metricName, config) {
    const base = metricName.split('{')[0];
    for (const c of config) {
        for (const pattern of c.metrics) {
            if (new RegExp(`^${pattern.replace('.*', '.*')}$`).test(base)) {
                return c.category;
            }
        }
    }
    return 'Other';
}

// Красивые названия для метрик по секциям
const METRIC_LABELS = {
    KPI: {
        tx_pool_size: 'Transaction Pool',
        jetty_server_requests_seconds_avg: 'API Response Time (avg)',
        process_cpu_usage: 'CPU Usage',
        jvm_gc_pause_seconds_sum: 'GC Pause (s)',
        'postgres_connections{database="db01"}': 'DB Connections',
        'postgres_locks{database="db01"}': 'Postgres Locks',
        'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}': 'JVM Memory Used',
        system_load_average_1m: 'System Load (1m)',
        jetty_server_requests_seconds_count: 'Jetty Requests Count',
        'postgres_rows_inserted_total{database="db01"}': 'Rows Inserted'
    },
    Transactions: {
        'postgres_transactions_total{database="db01"}': 'Total Transactions',
        'postgres_rows_updated_total{database="db01"}': 'Rows Updated',
        'postgres_rows_deleted_total{database="db01"}': 'Rows Deleted'
    },
    PostgreSQL: {
        'postgres_connections{database="db01"}': 'Active Connections',
        'postgres_locks{database="db01"}': 'Active Locks',
        'postgres_blocks_reads_total{database="db01"}': 'Blocks Read',
        'postgres_rows_inserted_total{database="db01"}': 'Rows Inserted',
        postgres_rows_updated_total: 'Rows Updated'
    },
    JVM: {
        jvm_gc_pause_seconds_sum: 'GC Pause Time',
        'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}': 'Memory Used',
        jvm_threads_live_threads: 'Live Threads',
        jvm_classes_loaded_classes: 'Loaded Classes'
    },
    Jetty: {
        jetty_server_requests_seconds_avg: 'Avg Response Time',
        jetty_connections_current_connections: 'Current Connections',
        jetty_connections_bytes_in_bytes_sum: 'Bytes In',
        jetty_connections_bytes_out_bytes_sum: 'Bytes Out'
    },
    System: {
        process_cpu_usage: 'CPU Usage',
        system_load_average_1m: 'Load Average (1m)',
        system_cpu_count: 'CPU Count'
    }
};

// Обновляю тултипы для точного соответствия ТЗ
const METRIC_TOOLTIPS = {
    KPI: {
        tx_pool_size: 'Кол-во транзакций в пуле ожидания. Рост = перегрузка сети.',
        jetty_server_requests_seconds_avg: 'Среднее время ответа API. Рост = риск таймаутов.',
        process_cpu_usage: 'Загрузка CPU процесса узла. >85% — узкое место.',
        jvm_gc_pause_seconds_sum: 'Общее время пауз GC. >1–3 сек = замирание JVM.',
        'postgres_connections{database="db01"}': 'Активные подключения к БД. Рост = близость к лимиту.',
        'postgres_locks{database="db01"}': 'Активные блокировки. Рост = тормоза БД.',
        'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}': 'Использование heap. Рост = давление на GC.',
        system_load_average_1m: 'Системная нагрузка. >2 — CPU/память на пределе.',
        jetty_server_requests_seconds_count: 'Всего HTTP-запросов. Показывает общий уровень нагрузки.',
        'postgres_rows_inserted_total{database="db01"}': 'Вставки в БД. Рост = интенсивная запись.'
    },
    Transactions: {
        'postgres_transactions_total{database="db01"}': 'Всего транзакций в БД.',
        'postgres_rows_updated_total{database="db01"}': 'Кол-во UPDATE-запросов в БД.',
        'postgres_rows_deleted_total{database="db01"}': 'Удаления. Много = очистка/нагрузка.'
    },
    PostgreSQL: {
        'postgres_connections{database="db01"}': 'Соединения с БД. Повтор KPI.',
        'postgres_locks{database="db01"}': 'Заблокированные ресурсы. Повтор KPI.',
        'postgres_blocks_reads_total{database="db01"}': 'Чтения с диска. Рост = плохой план запроса.',
        'postgres_rows_inserted_total{database="db01"}': 'Вставки в БД. Повтор из KPI.',
        postgres_rows_updated_total: 'Повтор.'
    },
    JVM: {
        jvm_gc_pause_seconds_sum: 'Повтор KPI',
        'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}': 'Использование памяти. Повтор KPI',
        jvm_threads_live_threads: 'Кол-во активных потоков. Рост = утечка/нагрузка.',
        jvm_classes_loaded_classes: 'Загруженные классы. Рост = возможная утечка.'
    },
    Jetty: {
        jetty_server_requests_seconds_avg: 'Повтор KPI',
        jetty_connections_current_connections: 'Активные HTTP-соединения. Рост = API-нагрузка.',
        jetty_connections_bytes_in_bytes_sum: 'Суммарный входящий трафик.',
        jetty_connections_bytes_out_bytes_sum: 'Суммарный исходящий трафик.'
    },
    System: {
        process_cpu_usage: 'Повтор KPI.',
        system_load_average_1m: 'Повтор KPI.',
        system_cpu_count: 'Кол-во ядер. Для понимания контекста нагрузки.'
    }
};

function getMetricTooltip(section, metric, hasData) {
    let text = (METRIC_TOOLTIPS[section] && METRIC_TOOLTIPS[section][metric]) ? METRIC_TOOLTIPS[section][metric] : metric;
    if (!hasData) {
        text += '\n\nДанные временно недоступны. Значение отображается как 0.';
    }
    return text;
}

// Дефолтные значения секций и prominent-метрик (скопировать из backend/config.py)
const DEFAULT_METRICS_CONFIG = [
    { category: 'Transactions', metrics: [
        'postgres_transactions_total{database="db01"}',
        'postgres_rows_updated_total{database="db01"}',
        'postgres_rows_deleted_total{database="db01"}'
    ], display: 'counter', color: '#8e44ad', priority: 1 },
    { category: 'PostgreSQL', metrics: [
        'postgres_connections{database="db01"}',
        'postgres_locks{database="db01"}',
        'postgres_blocks_reads_total{database="db01"}',
        'postgres_rows_inserted_total{database="db01"}',
        'postgres_rows_updated_total',
        'postgres_transactions_total'
    ], display: 'compact', color: '#3498db', priority: 2 },
    { category: 'JVM', metrics: [
        'jvm_gc_pause_seconds_sum',
        'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}',
        'jvm_threads_live_threads',
        'jvm_classes_loaded_classes'
    ], display: 'compact', color: '#27ae60', priority: 3 },
    { category: 'Jetty', metrics: [
        'jetty_server_requests_seconds_avg',
        'jetty_connections_current_connections',
        'jetty_connections_bytes_in_bytes_sum',
        'jetty_connections_bytes_out_bytes_sum'
    ], display: 'compact', color: '#e74c3c', priority: 4 },
    { category: 'System', metrics: [
        'process_cpu_usage',
        'system_load_average_1m',
        'system_cpu_count'
    ], display: 'compact', color: '#f39c12', priority: 5 }
];

const DEFAULT_PROMINENT_METRICS = {
    tx_pool_size: { title: 'Transaction Pool', unit: '', color: '#145a32', format: 'fixed0' },
    jetty_server_requests_seconds_avg: { title: 'API Response Time (avg)', unit: 's', color: '#145a32', format: 'fixed2' },
    process_cpu_usage: { title: 'CPU Usage', unit: '%', color: '#145a32', format: 'fixed2' },
    'postgres_connections{database="db01"}': { title: 'DB Connections', unit: '', color: '#145a32', format: 'fixed0' },
    'postgres_locks{database="db01"}': { title: 'Postgres Locks', unit: '', color: '#145a32', format: 'fixed0' },
    jvm_gc_pause_seconds_sum: { title: 'GC Pause (s)', unit: 's', color: '#145a32', format: 'fixed2' },
    'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}': { title: 'JVM Memory Used', unit: 'B', color: '#145a32', format: 'fixed0' },
    system_load_average_1m: { title: 'System Load (1m)', unit: '', color: '#145a32', format: 'fixed2' },
    jetty_server_requests_seconds_count: { title: 'Jetty Requests Count', unit: '', color: '#145a32', format: 'fixed0' },
    'postgres_rows_inserted_total{database="db01"}': { title: 'Rows Inserted', unit: '', color: '#145a32', format: 'fixed0' }
};

function getEmptyDashboardData() {
    const prominent = Object.keys(DEFAULT_PROMINENT_METRICS);
    const allSections = Object.keys(METRIC_LABELS);
    const allMetrics = {};
    for (const section of allSections) {
        for (const key in METRIC_LABELS[section]) {
            allMetrics[key] = 0.0;
        }
    }
    return {
        metrics: allMetrics,
        config: DEFAULT_METRICS_CONFIG,
        prominent: DEFAULT_PROMINENT_METRICS,
        last_updated: Math.floor(Date.now() / 1000),
        error: 'no_data'
    };
}

function showNoDataBanner() {
    let banner = document.getElementById('no-data-banner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'no-data-banner';
        banner.className = 'alert-error';
        banner.textContent = 'Нет связи с сервером метрик. Отображаются нули.';
        document.querySelector('.container').prepend(banner);
    }
    banner.style.display = 'block';
}

function hideNoDataBanner() {
    const banner = document.getElementById('no-data-banner');
    if (banner) banner.style.display = 'none';
}

async function updateDashboard() {
    toggleSpinner(true);
    try {
        const resp = await fetch('/data');
        const data = await resp.json();
        toggleSpinner(false);
        
        if (!data || typeof data !== 'object' || data.error) {
            showNoDataBanner();
            const emptyData = getEmptyDashboardData();
            await updateProminentMetrics(emptyData);
            await updateMetricsSections(emptyData);
            await updateTransactionsSection(emptyData);
            document.getElementById('last-updated').textContent = '-';
            return;
        }
        
        hideNoDataBanner();
        await updateProminentMetrics(data);
        await updateMetricsSections(data);
        await updateTransactionsSection(data);
        document.getElementById('last-updated').textContent =
            new Date(data.last_updated * 1000).toLocaleString();
    } catch (err) {
        toggleSpinner(false);
        showNoDataBanner();
        const emptyData = getEmptyDashboardData();
        await updateProminentMetrics(emptyData);
        await updateMetricsSections(emptyData);
        await updateTransactionsSection(emptyData);
        document.getElementById('last-updated').textContent = '-';
    }
}

// Запускаем polling истории при загрузке страницы
startHistoryPolling();

// Основной интервал обновления дашборда
setInterval(updateDashboard, UPDATE_INTERVAL);
updateDashboard();