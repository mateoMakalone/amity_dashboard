# Amity Metrics Dashboard

## Описание

**Amity Metrics Dashboard** — это веб-приложение для мониторинга ключевых метрик инфраструктуры и приложений на основе данных Prometheus. Дашборд позволяет отслеживать состояние PostgreSQL, JVM, Jetty, System и бизнес-метрик в реальном времени, с цветовой индикацией порогов и подробными тултипами.

## Основные возможности
- Визуализация Key Performance Indicators (KPI) с пороговой подсветкой (green/yellow/red)
- Секции: KPI, Transactions (график), PostgreSQL, JVM, Jetty, System
- История метрик и графики (Plotly.js)
- Кастомные тултипы с бизнес-описаниями и диагностикой
- Отображение всех метрик даже при отсутствии данных (debug-режим)
- Гибкая архитектура для расширения и кастомизации

## Структура проекта
```
amity_dashboard/
├── app/
│   ├── __init__.py
│   ├── config.py         # Конфиг секций, метрик, порогов
│   ├── metrics.py        # Логика сбора и агрегации метрик
│   ├── parser.py         # Парсер Prometheus-метрик с фильтрацией по лейблам
│   ├── routes.py         # Flask endpoints
│   ├── static/
│   │   ├── css/styles.css
│   │   └── js/dashboard.js
│   └── templates/dashboard.html
├── run.py                # Точка входа (Flask)
└── README.md
```

## Запуск
1. Установите зависимости (Python 3.8+):
   ```bash
   pip install flask requests
   ```
2. Укажите адрес Prometheus/экспортера в `app/config.py`:
   ```python
   METRICS_URL = "http://your-prometheus-server:9090/metrics"
   ```
Приложение периодически запрашивает этот адрес и парсит ответ в формате Prometheus.
3. Запустите сервер:
   ```bash
   python run.py
   ```
4. Откройте [http://localhost:5000](http://localhost:5000) в браузере.

## Кастомизация и расширение
- **Добавление метрик:**
  - В `config.py` добавьте нужные метрики и секции (с поддержкой лейблов).
  - В `parser.py` реализуйте фильтрацию/агрегацию для новых метрик.
- **Пороговые значения:**
  - Настраиваются в `dashboard.js` (KPI_THRESHOLDS) и `config.py`.
- **Тултипы:**
  - Описания для метрик настраиваются в JS-объекте `METRIC_TOOLTIPS`.

## Архитектурные особенности
- **Дашборд всегда отображает все секции и метрики** (даже если нет данных — показывается 0.0 и тултип о недоступности).
- **История метрик** хранится в памяти (rolling window, настраивается в config.py).
- **График Transactions** реализован как динамический Plotly-график по истории.
- **Frontend** полностью на JS (без фреймворков), легко интегрируется в любой Flask-проект.

## Пример бизнес-метрик (KPI)
- Transaction Pool: `tx_pool_size`
- API Response Time (avg): `jetty_server_requests_seconds_avg` (вычисляется на бэке)
- CPU Usage: `process_cpu_usage`
 - GC Pause (major): `gc_pause_time`
- DB Connections: `postgres_connections{database="db01"}`
- Dead Rows: `postgres_dead_rows`
- ...и другие (см. config и JS)

## Контакты и поддержка
- [GitHub Issues](https://github.com/mateoMakalone/amity_dashboard/issues)
- Pull requests приветствуются!
