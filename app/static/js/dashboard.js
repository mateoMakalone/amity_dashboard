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

function updateDashboard() {
    toggleSpinner(true);
    fetch('/data')
        .then(r => r.json())
        .then(data => {
            toggleSpinner(false);
            if (!data || typeof data !== 'object' || data.error) {
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').textContent = data && data.error ? `Error: ${data.error}` : 'No data received';
                return;
            }
            updateProminentMetrics(data);
            updateResponseTimes(data);
            updateMetricsSections(data);
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

/**
 * Обновляет ключевые метрики
 * @param {object} data
 */
function updateProminentMetrics(data) {
    const container = document.getElementById('prominent-metrics');
    container.innerHTML = '';
    for (const [metricName, config] of Object.entries(data.prominent)) {
        if (data.metrics[metricName] !== undefined) {
            const value = data.metrics[metricName];
            const formatType = config.format || "fixed2";
            const formatter = formatFunctions[formatType] || formatFunctions.fixed2;
            const formattedValue = formatter(value);
            const card = document.createElement('div');
            card.className = `key-metric-card card`;
            card.innerHTML = `
                <div class="key-metric-name">${config.title}</div>
                <div class="key-metric-value">${formattedValue}${config.unit ? ' ' + config.unit : ''}</div>
            `;
            fadeIn(card);
            container.appendChild(card);
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
        const prefix = pattern.replace(/\W.*$/, '');
        if (metricName.startsWith(prefix + '_')) {
            return metricName.slice(prefix.length + 1);
        }
    }
    return metricName;
}

function updateMetricsSections(data) {
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
    for (const category of orderedCategories) {
        let section = oldSections[category];
        const categoryConfig = getCategoryConfig(category, data.config);
        const color = categoryConfig.color || '#eee';
        if (!section) {
            section = document.createElement('section');
            section.className = 'metrics-section';
            section.setAttribute('data-category', category);
            section.innerHTML = `<h2 class="section-title">${category}</h2><div class="metrics-grid" id="section-${category}"></div>`;
            container.appendChild(section);
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
                    <div class="metric-name" title="${name}">${toTitleCase(shortName)}</div>
                    <div class="metric-value"></div>
                `;
                grid.appendChild(card);
            }
            const valueDiv = card.querySelector('.metric-value');
            const newValue = data.metrics[name].toFixed(2);
            if (valueDiv.textContent !== newValue) {
                valueDiv.textContent = newValue;
                fadeIn(valueDiv);
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

setInterval(updateDashboard, UPDATE_INTERVAL);
updateDashboard();