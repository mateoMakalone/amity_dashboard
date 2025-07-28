
let lastUpdateId = 0;
const sectionDataLoaded = {};

async function fetchWithRetry(url, retries = 2, delay = 500) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response;
    } catch (err) {
        if (retries > 0) {
            console.warn(`Retrying ${url}, attempts left: ${retries}`);
            await new Promise(res => setTimeout(res, delay));
            return fetchWithRetry(url, retries - 1, delay * 2);
        }
        throw err;
    }
}

function updateMetricCard(metricId, data) {
    const card = document.getElementById(`card-${metricId}`);
    if (card) {
        card.querySelector('.metric-value').textContent = data.currentValue;
        updateGraph(metricId, data.history);
    }
}

function updateGraph(metricId, newData) {
    const graphDiv = document.getElementById(`graph-${metricId}`);
    if (!graphDiv) return;
    Plotly.react(graphDiv, [{
        x: newData.timestamps,
        y: newData.values,
        mode: 'lines',
        line: { simplify: false }
    }], {
        margin: { t: 20 }
    }, { responsive: true });
}

async function loadSectionData(section) {
    const resp = await fetchWithRetry(`/api/metrics/history?section=${section}`);
    const data = await resp.json();
    for (const [metricId, metricData] of Object.entries(data)) {
        updateMetricCard(metricId, metricData);
    }
}

document.querySelectorAll('.section-toggle').forEach(toggle => {
    toggle.addEventListener('click', async (e) => {
        const section = e.target.dataset.section;
        if (!sectionDataLoaded[section]) {
            await loadSectionData(section);
            sectionDataLoaded[section] = true;
        }
    });
});

async function safeUpdateMetrics() {
    const updateId = ++lastUpdateId;
    const response = await fetchWithRetry('/api/metrics/batch');
    if (updateId !== lastUpdateId) return;
    const data = await response.json();
    for (const [metricId, metricData] of Object.entries(data)) {
        updateMetricCard(metricId, metricData);
    }
}

setInterval(safeUpdateMetrics, 5000);
