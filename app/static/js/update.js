let lastUpdateId = 0;

async function fetchWithRetry(url, retries = 3, delay = 500) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return resp;
        } catch (err) {
            if (attempt < retries) {
                console.warn(`Retry ${attempt} failed:`, err);
                await new Promise(res => setTimeout(res, delay));
            } else {
                throw err;
            }
        }
    }
}

function updateMetricCard(metricId, metricData) {
    const card = document.getElementById(`card-${metricId}`);
    if (!card) return;

    const valueElem = card.querySelector('.metric-value');
    if (valueElem) valueElem.textContent = metricData.current;

    const graphDiv = document.getElementById(`graph-${metricId}`);
    if (graphDiv && metricData.history) {
        const timestamps = metricData.history.map((_, i) => i);
        Plotly.react(graphDiv, [{
            x: timestamps,
            y: metricData.history,
            mode: 'lines',
            line: { simplify: false }
        }], { margin: { t: 20 } }, { responsive: true });
    }
}

async function updateAllMetrics() {
    const updateId = ++lastUpdateId;
    try {
        const resp = await fetchWithRetry('/api/metrics/batch');
        const data = await resp.json();

        if (updateId !== lastUpdateId) {
            console.warn('Skipping outdated update');
            return;
        }

        for (const [metricId, metricData] of Object.entries(data)) {
            updateMetricCard(metricId, metricData);
        }
    } catch (err) {
        console.error('Failed to update metrics:', err);
    }
}

// Запускаем обновление раз в 1 секунду
setInterval(updateAllMetrics, 1000);
updateAllMetrics();
