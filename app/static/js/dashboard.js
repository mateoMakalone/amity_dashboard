const formatFunctions = {
    fixed0: x => x.toFixed(0),
    fixed2: x => x.toFixed(2),
    fixed3: x => x.toFixed(3),
    roundFormat: x => Math.round(x).toLocaleString()
};

function updateDashboard() {
    fetch('/data')
        .then(r => r.json())
        .then(data => {
            document.getElementById('error').style.display = data.error ? 'block' : 'none';
            document.getElementById('error').textContent = data.error ? `Error: ${data.error}` : '';
            updateProminentMetrics(data);
            updateResponseTimes(data);
            updateMetricsSections(data);
            document.getElementById('last-updated').textContent =
                new Date(data.last_updated * 1000).toLocaleString();
        })
        .catch(err => {
            const errorEl = document.getElementById('error');
            errorEl.style.display = 'block';
            errorEl.textContent = `Request failed: ${err.message}`;
        });
}

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
            card.className = `key-metric-card`;
            card.innerHTML = `
                <div class="key-metric-name">${config.title}</div>
                <div class="key-metric-value">${formattedValue}${config.unit ? ' ' + config.unit : ''}</div>
            `;
            container.appendChild(card);
        }
    }
}

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
            card.className = 'response-card';
            card.innerHTML = `
                <div class="metric-name">${res.label}</div>
                <div class="response-value">${data.metrics[avgKey].toFixed(3)} s</div>
                <div class="metric-name">${formatFunctions.roundFormat(data.metrics[countKey])} requests</div>
            `;
            container.appendChild(card);
        }
    }
}

function updateMetricsSections(data) {
    const container = document.getElementById('metrics-sections');
    container.innerHTML = '';
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
    for (const category of orderedCategories) {
        const section = document.createElement('section');
        section.className = 'metrics-section';
        section.innerHTML = `<h2 class="section-title">${category}</h2><div class="metrics-grid" id="section-${category}"></div>`;
        const grid = section.querySelector('.metrics-grid');
        for (const name of categories[category]) {
            const card = document.createElement('div');
            card.className = 'metric-card';
            card.innerHTML = `
                <div class="metric-name" title="${name}">${name}</div>
                <div class="metric-value">${data.metrics[name].toFixed(2)}</div>
            `;
            grid.appendChild(card);
        }
        container.appendChild(section);
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

setInterval(updateDashboard, 1000);
updateDashboard();