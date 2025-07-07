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

// Словарь "человеческих" названий для base_name
const humanNames = {
    "tx_pool_size": "Transaction Pool",
    "process_cpu_usage": "CPU Usage",
    "system_cpu_usage": "System CPU Usage",
    "system_load_average_1m": "Load Average (1m)",
    "system_cpu_count": "CPU Count",
    "postgres_locks": "Locks",
    "postgres_connections": "Connections",
    "postgres_rows_inserted_total": "Rows Inserted",
    "postgres_rows_updated_total": "Rows Updated",
    "postgres_rows_fetched_total": "Rows Fetched",
    "postgres_rows_deleted_total": "Rows Deleted",
    "postgres_blocks_reads_total": "Blocks Reads Total",
    "postgres_buffers_checkpoint_total": "Buffers Checkpoint Total",
    "postgres_checkpoints_timed_total": "Checkpoints Timed Total",
    "postgres_checkpoints_requested_total": "Checkpoints Requested Total",
    "postgres_size": "Database Size",
    "postgres_transactions_total": "Transactions Total",
    "postgres_blocks_hits_total": "Blocks Hits Total",
    "postgres_temp_writes_bytes_total": "Temp Writes Bytes Total",
    "postgres_buffers_backend_total": "Buffers Backend Total",
    "postgres_buffers_clean_total": "Buffers Clean Total",
    "postgres_rows_dead": "Rows Dead",
    "jvm_memory_used_bytes": "Memory Used Bytes",
    "jvm_memory_committed_bytes": "Memory Committed Bytes",
    "jvm_memory_max_bytes": "Memory Max Bytes",
    "jvm_gc_pause_seconds_sum": "GC Pause Seconds Sum",
    "jvm_gc_pause_seconds_count": "GC Pause Seconds Count",
    "jvm_gc_pause_seconds_max": "GC Pause Seconds Max",
    "jvm_gc_memory_promoted_bytes_total": "GC Memory Promoted Bytes Total",
    "jvm_gc_memory_allocated_bytes_total": "GC Memory Allocated Bytes Total",
    "jvm_gc_max_data_size_bytes": "GC Max Data Size Bytes",
    "jvm_gc_live_data_size_bytes": "GC Live Data Size Bytes",
    "jvm_threads_live_threads": "Live Threads",
    "jvm_threads_daemon_threads": "Daemon Threads",
    "jvm_threads_peak_threads": "Peak Threads",
    "jvm_threads_started_threads_total": "Threads Started Total",
    "jvm_threads_states_threads": "Threads States Threads",
    "jvm_classes_loaded_classes": "Classes Loaded",
    "jvm_classes_unloaded_classes_total": "Classes Unloaded",
    "jvm_buffer_count_buffers": "Buffer Count Buffers",
    "jvm_buffer_memory_used_bytes": "Buffer Memory Used Bytes",
    "jvm_buffer_total_capacity_bytes": "Buffer Total Capacity Bytes",
    "jetty_server_requests_seconds_count": "Server Requests Seconds Count",
    "jetty_server_requests_seconds_sum": "Server Requests Seconds Sum",
    "jetty_server_requests_seconds_max": "Server Requests Seconds Max",
    "jetty_connections_current_connections": "Connections Current",
    "jetty_connections_max_connections": "Connections Max",
    "jetty_connections_messages_in_messages_total": "Connections Messages In",
    "jetty_connections_messages_out_messages_total": "Connections Messages Out",
    "jetty_connections_bytes_in_bytes_count": "Connections Bytes In (Count)",
    "jetty_connections_bytes_in_bytes_max": "Connections Bytes In (Max)",
    "jetty_connections_bytes_in_bytes_sum": "Connections Bytes In (Sum)",
    "jetty_connections_bytes_out_bytes_count": "Connections Bytes Out (Count)",
    "jetty_connections_bytes_out_bytes_max": "Connections Bytes Out (Max)",
    "jetty_connections_bytes_out_bytes_sum": "Connections Bytes Out (Sum)",
    // ... можно расширять ...
};

function getHumanName(metricName) {
    const base = metricName.split('{')[0];
    const labelMatch = metricName.match(/\{(.+)\}/);
    let labelStr = "";
    if (labelMatch) {
        // Преобразуем лейблы в красивый вид
        labelStr = labelMatch[1]
            .replace(/"/g, "")
            .replace(/,/g, ", ")
            .replace(/=/g, "=")
            .replace(/_/g, " ")
            .replace(/([a-z])([A-Z])/g, "$1 $2");
    }
    let name = humanNames[base] || toTitleCase(base.replace(/_/g, " "));
    if (labelStr) name += " (" + labelStr + ")";
    return name;
}

async function updateProminentMetrics(data) {
    const container = document.getElementById('prominent-metrics');
    // Не удаляем карточки, только обновляем значения и графики
    const oldCards = {};
    container.querySelectorAll('.key-metric-card').forEach(card => {
        oldCards[card.getAttribute('data-metric')] = card;
    });
    let insertAfter = container.querySelector('.section-title');
    const history = await fetchHistory();
    for (const [metricName, config] of Object.entries(data.prominent)) {
        if (data.metrics[metricName] !== undefined) {
            let card = oldCards[metricName];
            const category = getCategoryConfig(getMetricCategory(metricName, data.config), data.config);
            let shortTitle = config.title || getHumanName(metricName);
            const value = data.metrics[metricName];
            const formatType = config.format || "fixed2";
            const formatter = formatFunctions[formatType] || formatFunctions.fixed2;
            const formattedValue = formatter(value);
            if (!card) {
                card = document.createElement('div');
                card.className = `key-metric-card card`;
                card.setAttribute('data-metric', metricName);
                card.innerHTML = `
                    <div class=\"key-metric-name metric-name\" title=\"${metricName}\">${shortTitle}</div>
                    <div class=\"key-metric-value\"></div>
                    <div class=\"metric-history-plot\" id=\"plot-${metricName}\"></div>
                `;
                if (insertAfter && insertAfter.nextSibling) {
                    container.insertBefore(card, insertAfter.nextSibling);
                } else {
                    container.appendChild(card);
                }
                insertAfter = card;
            }
            // Обновляем только значение
            const valueDiv = card.querySelector('.key-metric-value');
            if (valueDiv.textContent !== formattedValue + (config.unit ? ' ' + config.unit : '')) {
                valueDiv.textContent = formattedValue + (config.unit ? ' ' + config.unit : '');
                fadeIn(valueDiv);
            }
            // Обновляем только данные графика
            const plotDiv = card.querySelector('.metric-history-plot');
            if (plotDiv && history[metricName]) {
                const x = history[metricName].map(([ts, _]) => new Date(ts * 1000));
                const y = history[metricName].map(([_, v]) => v);
                Plotly.react(plotDiv, [{x, y, type: 'scatter', mode: 'lines', line: {color: '#800000'}}], {
                    margin: {t: 10, b: 30, l: 40, r: 10},
                    height: 120,
                    xaxis: {showgrid: false, tickformat: '%H:%M:%S'},
                    yaxis: {showgrid: true, zeroline: false},
                    displayModeBar: false
                }, {displayModeBar: false});
            }
        }
    }
}

/**
 * Обновляет карточки времени отклика
 * @param {object} data
 */
function updateResponseTimes(data) {
    const container = document.getElementById('avg-times');
    container.innerHTML = '';
    const responses = [
        { type: 'POST', label: 'Average POST Response Time' },
        { type: 'GET', label: 'Average GET Response Time' }
    ];
    for (const res of responses) {
        const avgKey = `jetty_${res.type.toLowerCase()}_avg_time`;
        const countKey = `jetty_server_requests_seconds_count{method="${res.type}",outcome="SUCCESS",status="200",}`;
        if (data.metrics[avgKey] !== undefined) {
            const card = document.createElement('div');
            card.className = 'response-card card';
            card.innerHTML = `
                <div class="metric-name">${res.label}</div>
                <div class="response-value">${data.metrics[avgKey].toFixed(3)} s</div>
                <div class="metric-name">${formatFunctions.roundFormat(data.metrics[countKey])} requests</div>
            `;
            fadeIn(card);
            container.appendChild(card);
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

async function updateMetricsSections(data) {
    const container = document.getElementById('metrics-sections');
    const categories = {};
    for (const metricName in data.metrics) {
        if (data.prominent[metricName] || metricName.includes('_avg_time')) continue;
        const category = getMetricCategory(metricName, data.config);
        if (!categories[category]) categories[category] = [];
        categories[category].push(metricName);
    }
    const orderedCategories = data.config
        .sort((a, b) => a.priority - b.priority)
        .map(c => c.category)
        .filter(c => categories[c]);
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
            let card = oldCards[name];
            const shortName = stripCategoryPrefix(name, categoryConfig);
            if (!card) {
                card = document.createElement('div');
                card.className = 'metric-card card';
                card.setAttribute('data-metric', name);
                card.innerHTML = `
                    <div class=\"metric-name\" title=\"${name}\">${getHumanName(name)}</div>
                    <div class=\"metric-value\"></div>
                    <div class=\"metric-history-plot\" id=\"plot-${name}\"></div>
                `;
                grid.appendChild(card);
            } else {
                // Если карточка уже есть, но нет графика — добавить
                if (!card.querySelector('.metric-history-plot')) {
                    const plotDiv = document.createElement('div');
                    plotDiv.className = 'metric-history-plot';
                    plotDiv.id = `plot-${name}`;
                    card.appendChild(plotDiv);
                }
            }
            const valueDiv = card.querySelector('.metric-value');
            const newValue = data.metrics[name].toFixed(2);
            if (valueDiv.textContent !== newValue) {
                valueDiv.textContent = newValue;
                fadeIn(valueDiv);
            }
            // Только для секции System рисуем график
            if (category === 'System') {
                const plotDiv = card.querySelector('.metric-history-plot');
                if (plotDiv && history[name]) {
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

function updateDashboard() {
    toggleSpinner(true);
    fetch('/data')
        .then(r => r.json())
        .then(async data => {
            toggleSpinner(false);
            if (!data || typeof data !== 'object' || data.error) {
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').textContent = data && data.error ? `Error: ${data.error}` : 'No data received';
                return;
            }
            await updateProminentMetrics(data);
            updateResponseTimes(data);
            await updateMetricsSections(data);
            document.getElementById('last-updated').textContent =
                new Date(data.last_updated * 1000).toLocaleString();
        })
        .catch(err => {
            toggleSpinner(false);
            const errorEl = document.getElementById('error');
            errorEl.style.display = 'block';
            errorEl.textContent = `Request failed: ${err.message}`;
        });
}

setInterval(updateDashboard, UPDATE_INTERVAL);
updateDashboard();