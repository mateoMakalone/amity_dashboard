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
 * Добавляет fade-in анимацию к элементу
 * @param {HTMLElement} el
 */
function fadeIn(el) {
    el.style.opacity = 0;
    el.style.transition = 'opacity 0.5s';
    requestAnimationFrame(() => {
        el.style.opacity = 1;
    });
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

async function fetchHistory() {
    const resp = await fetch('/history');
    return await resp.json();
}

// Получить список игнорируемых метрик из data.config или локально
function getIgnoreMetrics(config) {
    // Ищем IGNORE_METRICS в config, если нет — используем дефолт
    if (config && config.IGNORE_METRICS) return config.IGNORE_METRICS;
    return [
        "postgres_buffers_clean_total",
        "postgres_rows_dead",
        "postgres_blocks_hits_total",
        "postgres_checkpoints_requested_total",
        "postgres_size",
        "jvm_buffer_count_buffers",
        "jvm_buffer_memory_used_bytes",
        "jvm_buffer_total_capacity_bytes",
        "jvm_classes_unloaded_classes_total",
        "jvm_gc_live_data_size_bytes",
        "jvm_memory_committed_bytes",
        "jvm_memory_max_bytes",
        "jetty_connections_bytes_in_bytes_max",
        "jetty_connections_bytes_out_bytes_max",
        "jetty_connections_messages_in_messages_total",
        "jetty_connections_messages_out_messages_total",
        "jetty_server_dispatches_open_seconds_max",
        "jetty_server_async_waits_operations",
        "jetty_server_async_dispatches_total",
        "jetty_server_async_expires_total"
    ];
}

function isIgnoredMetric(metricName, config) {
    const ignore = getIgnoreMetrics(config);
    // Фильтрация по base_name
    const base = metricName.split('{')[0];
    if (ignore.includes(base)) return true;
    // Спец. фильтр для jvm_memory_used_bytes с area=nonheap
    if (base === 'jvm_memory_used_bytes' && metricName.includes('area="nonheap"')) return true;
    // Спец. фильтр для jvm_memory_committed_bytes по CodeHeap, Metaspace, Compressed Class Space
    if (base === 'jvm_memory_committed_bytes' &&
        (metricName.includes('CodeHeap') || metricName.includes('Metaspace') || metricName.includes('Compressed Class Space')))
        return true;
    // Спец. фильтр для jvm_memory_used_bytes по CodeHeap, Metaspace, Compressed Class Space
    if (base === 'jvm_memory_used_bytes' &&
        (metricName.includes('CodeHeap') || metricName.includes('Metaspace') || metricName.includes('Compressed Class Space')))
        return true;
    return false;
}

// Фильтрация в KPI
async function updateProminentMetrics(data) {
    const container = document.getElementById('prominent-metrics');
    const oldCards = {};
    container.querySelectorAll('.key-metric-card').forEach(card => {
        oldCards[card.getAttribute('data-metric')] = card;
    });
    let insertAfter = container.querySelector('.section-title');
    const history = await fetchHistory();
    // Сортируем KPI по приоритету (desc) из PROMINENT_METRICS
    const prominentConfig = data.prominent || window.PROMINENT_METRICS || {};
    const kpiData = data.kpi || {};
    const sortedProminent = Object.entries(prominentConfig)
        .filter(([metricName, config]) => kpiData[metricName] !== undefined)
        .sort((a, b) => (b[1].priority || 0) - (a[1].priority || 0));
    for (const [metricName, config] of sortedProminent) {
        if (!kpiData || kpiData[metricName] === undefined || kpiData[metricName] === null || isNaN(kpiData[metricName])) continue;
        const value = kpiData[metricName];
        if (value === undefined) continue;
        let card = oldCards[metricName];
        let shortTitle = config.title || metricName;
        const formatType = config.format || "fixed2";
        const formatter = formatFunctions[formatType] || formatFunctions.fixed2;
        let formattedValue = formatter(value);
        // Особый случай: process_cpu_usage — отображать как %
        if (metricName === 'process_cpu_usage') {
            formattedValue = formatter(value * 100);
            if (!config.unit) config.unit = '%';
        }
        // Цветовая индикация
        let state = 'ok';
        const colorMap = { ok: '#27ae60', warning: '#f39c12', critical: '#e74c3c', default: '#bbb' };
        let cardStyle = '';
        let plotColor = colorMap.default;
        // Для jvm_memory_used_bytes{area="heap",id="Tenured Gen"} подсветка только если есть max и пороги
        let hasThresholds = typeof config.warning === 'number' || typeof config.critical === 'number';
        let warning = config.warning;
        let critical = config.critical;
        if (metricName === 'jvm_memory_used_bytes{area="heap",id="Tenured Gen"}') {
            const max = kpiData['jvm_memory_used_bytes{area="heap",id="Tenured Gen"}_max'];
            if (max) {
                warning = 0.75 * max;
                critical = 0.9 * max;
                hasThresholds = true;
            } else {
                hasThresholds = false;
            }
        }
        if (hasThresholds) {
            if (typeof critical === 'number' && value >= critical) state = 'critical';
            else if (typeof warning === 'number' && value >= warning) state = 'warning';
            cardStyle = `border-left: 6px solid ${colorMap[state]}; box-shadow: 0 2px 8px rgba(0,0,0,0.04);`;
            plotColor = colorMap[state];
        }
        // Tooltip
        let tooltip = `<b>${shortTitle}</b><br/>`;
        if (config.description) tooltip += `${config.description}<br/>`;
        if (config.why) tooltip += `<i>${config.why}</i><br/>`;
        if (typeof config.warning === 'number') tooltip += `Warning: ${config.warning}<br/>`;
        if (typeof config.critical === 'number') tooltip += `Critical: ${config.critical}`;
        if (!card) {
            card = document.createElement('div');
            card.className = `key-metric-card card`;
            card.setAttribute('data-metric', metricName);
            card.setAttribute('title', '');
            card.innerHTML = `
                <div class=\"key-metric-name metric-name\" title=\"${shortTitle}\">${shortTitle}</div>
                <div class=\"key-metric-value\"></div>
                <div class=\"metric-history-plot\" id=\"plot-${metricName}\"></div>
                <div class=\"kpi-tooltip\" style=\"display:none;position:absolute;z-index:10;background:#fff;border:1px solid #bbb;padding:8px 12px;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,0.08);font-size:0.95em;max-width:320px;\"></div>
            `;
            card.style = cardStyle;
            // Tooltip events
            card.addEventListener('mouseenter', function(e) {
                const tip = card.querySelector('.kpi-tooltip');
                tip.innerHTML = tooltip;
                tip.style.display = 'block';
                tip.style.left = (e.offsetX + 20) + 'px';
                tip.style.top = (e.offsetY + 10) + 'px';
            });
            card.addEventListener('mousemove', function(e) {
                const tip = card.querySelector('.kpi-tooltip');
                tip.style.left = (e.offsetX + 20) + 'px';
                tip.style.top = (e.offsetY + 10) + 'px';
            });
            card.addEventListener('mouseleave', function() {
                const tip = card.querySelector('.kpi-tooltip');
                tip.style.display = 'none';
            });
            if (insertAfter && insertAfter.nextSibling) {
                container.insertBefore(card, insertAfter.nextSibling);
            } else {
                container.appendChild(card);
            }
            insertAfter = card;
        }
        // Обновляем только значение и стиль
        const valueDiv = card.querySelector('.key-metric-value');
        if (valueDiv.textContent !== formattedValue + (config.unit ? ' ' + config.unit : '')) {
            valueDiv.textContent = formattedValue + (config.unit ? ' ' + config.unit : '');
            fadeIn(valueDiv);
        }
        card.style = cardStyle;
        // Обновляем только данные графика
        const plotDiv = card.querySelector('.metric-history-plot');
        if (!(plotDiv && history && history[metricName] && Array.isArray(history[metricName]) && history[metricName].length > 0)) {
            if (!history || !Array.isArray(history[metricName]) || history[metricName].length === 0) {
                console.warn('Нет истории для KPI-метрики:', metricName, history ? history[metricName] : undefined);
            }
        } else {
            const x = history[metricName].map(([ts, _]) => new Date(ts * 1000));
            const y = history[metricName].map(([_, v]) => v);
            Plotly.react(plotDiv, [{x, y, type: 'scatter', mode: 'lines', line: {color: plotColor}}], {
                margin: {t: 10, b: 30, l: 40, r: 10},
                height: 120,
                xaxis: {showgrid: false, tickformat: '%H:%M:%S'},
                yaxis: {showgrid: true, zeroline: false},
                displayModeBar: false
            }, {displayModeBar: false});
        }
    }
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

// Фильтрация в секциях
async function updateMetricsSections(data) {
    const container = document.getElementById('metrics-sections');
    const categories = {};
    for (const metricName in data.metrics) {
        if (data.prominent[metricName] || metricName.includes('_avg_time')) continue;
        if (isIgnoredMetric(metricName, data.config)) continue;
        // Фильтрация: только определённые и числовые метрики
        if (typeof data.metrics[metricName] !== 'number' || isNaN(data.metrics[metricName])) continue;
        const category = getMetricCategory(metricName, data.config);
        if (!categories[category]) categories[category] = [];
        categories[category].push(metricName);
    }
    // Секции: System всегда после KPI, остальные — по приоритету
    const systemCategory = data.config.find(c => c.category === 'System');
    const otherCategories = data.config
        .filter(c => c.category !== 'System')
        .sort((a, b) => a.priority - b.priority)
        .map(c => c.category)
        .filter(c => categories[c]);
    const orderedCategories = [];
    if (systemCategory && categories['System']) orderedCategories.push('System');
    orderedCategories.push(...otherCategories);
    const oldSections = {};
    container.querySelectorAll('.metrics-section').forEach(sec => {
        oldSections[sec.getAttribute('data-category')] = sec;
    });
    // Получаем историю для всех метрик
    const history = await fetchHistory();
    for (const category of orderedCategories) {
        let section = oldSections[category];
        const categoryConfig = getCategoryConfig(category, data.config);
        const color = categoryConfig.color || '#eee';
        if (!section) {
            section = document.createElement('section');
            section.className = 'metrics-section';
            section.setAttribute('data-category', category);
            section.innerHTML = `<h2 class=\"section-title\">${category}</h2><div class=\"metrics-grid\" id=\"section-${category}\"></div>`;
            container.appendChild(section);
        } else {
            let title = section.querySelector('.section-title');
            if (!title) {
                title = document.createElement('h2');
                title.className = 'section-title';
                title.textContent = category;
                section.prepend(title);
            } else {
                title.textContent = category;
            }
        }
        section.style.borderLeft = `6px solid ${color}`;
        const grid = section.querySelector('.metrics-grid');
        const oldCards = {};
        grid.querySelectorAll('.metric-card').forEach(card => {
            oldCards[card.getAttribute('data-metric')] = card;
        });
        for (const name of categories[category]) {
            try {
                if (!data.metrics || typeof data.metrics[name] !== 'number' || isNaN(data.metrics[name])) {
                    console.warn('Нет метрики или не число:', name, data.metrics ? data.metrics[name] : undefined);
                    continue;
                }
                let card = oldCards[name];
                const shortName = stripCategoryPrefix(name, categoryConfig);
                if (!card) {
                    card = document.createElement('div');
                    card.className = 'metric-card card';
                    card.setAttribute('data-metric', name);
                    card.innerHTML = `
                        <div class="metric-name" title="${name}">${toTitleCase(shortName)}</div>
                        <div class="metric-value"></div>
                        <div class="metric-history-plot" id="plot-${name}"></div>
                    `;
                    grid.appendChild(card);
                }
                const valueDiv = card.querySelector('.metric-value');
                const newValue = data.metrics[name].toFixed(2);
                if (valueDiv.textContent !== newValue) {
                    valueDiv.textContent = newValue;
                    fadeIn(valueDiv);
                }
                // Только для секции System рисуем график, если есть история
                if (category === 'System') {
                    const plotDiv = card.querySelector('.metric-history-plot');
                    if (!(plotDiv && history && Array.isArray(history[name]) && history[name].length > 0)) {
                        if (!history || !Array.isArray(history[name]) || history[name].length === 0) {
                            console.warn('Нет истории для метрики:', name, history ? history[name] : undefined);
                        }
                        continue;
                    }
                    const x = history[name].map(([ts, _]) => new Date(ts * 1000));
                    const y = history[name].map(([_, v]) => v);
                    Plotly.react(plotDiv, [{x, y, type: 'scatter', mode: 'lines', line: {color: color}}], {
                        margin: {t: 10, b: 30, l: 40, r: 10},
                        height: 120,
                        xaxis: {showgrid: false, tickformat: '%H:%M:%S'},
                        yaxis: {showgrid: true, zeroline: false},
                        displayModeBar: false
                    }, {displayModeBar: false});
                }
            } catch (err) {
                logJsError(`updateMetricsSections: ${name} (${category})`, err);
            }
        }
    }
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

function logJsError(context, err) {
    let logDiv = document.getElementById('js-error-log');
    if (!logDiv) {
        logDiv = document.createElement('div');
        logDiv.id = 'js-error-log';
        logDiv.style = 'position:fixed;bottom:0;left:0;right:0;max-height:200px;overflow:auto;background:#fff3f3;color:#c0392b;font-size:13px;padding:8px 16px;border-top:2px solid #e74c3c;z-index:9999;';
        document.body.appendChild(logDiv);
    }
    const msg = `[${new Date().toLocaleTimeString()}] JS ERROR in ${context}: ${err && err.stack ? err.stack : err}`;
    const p = document.createElement('div');
    p.textContent = msg;
    logDiv.appendChild(p);
    // Оставляем только последние 20 ошибок
    while (logDiv.children.length > 20) logDiv.removeChild(logDiv.firstChild);
}

function updateDashboard() {
    toggleSpinner(true);
    fetch('/data')
        .then(r => r.json())
        .then(async data => {
            try {
                toggleSpinner(false);
                if (!data || typeof data !== 'object' || data.error) {
                    document.getElementById('error').style.display = 'block';
                    document.getElementById('error').textContent = data && data.error ? `Error: ${data.error}` : 'No data received';
                    return;
                }
                try {
                    await updateProminentMetrics(data);
                } catch (err) {
                    const errorEl = document.getElementById('error');
                    errorEl.style.display = 'block';
                    errorEl.textContent = `KPI error: ${err.message}`;
                    logJsError('updateProminentMetrics', err);
                }
                try {
                    await updateMetricsSections(data);
                } catch (err) {
                    const errorEl = document.getElementById('error');
                    errorEl.style.display = 'block';
                    errorEl.textContent = `Section error: ${err.message}`;
                    logJsError('updateMetricsSections', err);
                }
                document.getElementById('last-updated').textContent =
                    new Date(data.last_updated * 1000).toLocaleString();
            } catch (err) {
                toggleSpinner(false);
                const errorEl = document.getElementById('error');
                errorEl.style.display = 'block';
                errorEl.textContent = `Request failed: ${err.message}`;
                logJsError('updateDashboard', err);
            }
        })
        .catch(err => {
            toggleSpinner(false);
            const errorEl = document.getElementById('error');
            errorEl.style.display = 'block';
            errorEl.textContent = `Request failed: ${err.message}`;
            logJsError('fetch/data', err);
        });
}

setInterval(updateDashboard, UPDATE_INTERVAL);
updateDashboard();