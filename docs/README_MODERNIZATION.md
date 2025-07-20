# 🚀 Модернизация KPI Dashboard

## 📋 Обзор изменений

Модернизированный KPI Dashboard теперь поддерживает:

### ✅ Реализованные функции

1. **Прямые запросы к Prometheus API**
   - Эндпоинт `/api/prometheus/query_range` для проксирования запросов
   - Поддержка MOCK_MODE для тестирования
   - Обработка ошибок Prometheus

2. **Конфигурируемые KPI-метрики**
   - Массив `KPI_METRICS_CONFIG` в `config.py`
   - Поддержка PromQL запросов
   - Настраиваемые пороги (warning/critical)
   - Цветовая схема для каждой метрики

3. **Интервалы времени**
   - Глобальный селектор интервалов (15/30/45/60 минут)
   - Синхронизация всех графиков
   - Динамическое обновление данных

4. **Интерактивные графики**
   - Линейные графики временных рядов (Plotly.js)
   - Гистограммы распределения значений
   - Адаптивный дизайн
   - Hover-подсказки

5. **Экспорт отчётов**
   - Кнопка "Экспорт отчёта"
   - Standalone HTML с интерактивными графиками
   - Автоматическое скачивание

6. **Современный UI**
   - Сетка KPI-карточек
   - Статусные индикаторы (OK/Warning/Critical)
   - Адаптивный дизайн
   - Русский интерфейс

## 🏗️ Архитектура

### Backend (Flask)

```
app/
├── config.py              # KPI_METRICS_CONFIG, TIME_INTERVALS
├── routes.py              # /api/prometheus/query_range, /api/kpi/config
├── metrics.py             # Существующая логика метрик
└── templates/
    └── dashboard.html     # Модернизированный шаблон
```

### Frontend (Vanilla JS + Plotly.js)

```
app/static/js/
└── dashboard.js           # Полностью переписанный JS
```

## 🔧 Конфигурация

### KPI-метрики (`config.py`)

```python
KPI_METRICS_CONFIG = [
    {
        "id": "api_response_time",
        "title": "Среднее время ответа API",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{outcome="SUCCESS",status="200"}[1m]))',
        "unit": "сек",
        "color": "#e74c3c",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.0}
    },
    # ... другие метрики
]
```

### Интервалы времени

```python
TIME_INTERVALS = [
    {"value": 15, "label": "15 минут"},
    {"value": 30, "label": "30 минут"}, 
    {"value": 45, "label": "45 минут"},
    {"value": 60, "label": "1 час"}
]
```

## 🚀 Запуск и тестирование

### 1. Запуск сервера

```bash
python run.py
```

Сервер запустится на `http://localhost:5000`

### 2. Тестирование API

```bash
# Конфигурация KPI
curl http://localhost:5000/api/kpi/config

# Прокси Prometheus
curl "http://localhost:5000/api/prometheus/query_range?query=system_cpu_usage&start=1640995200&end=1640998800&step=30"

# Главная страница
curl http://localhost:5000/
```

### 3. Автоматическое тестирование

```bash
python test_modernized_dashboard.py
```

## 📊 Функциональность

### KPI-карточки

Каждая KPI-карточка содержит:
- **Заголовок** с названием метрики
- **Текущее значение** с единицами измерения
- **Цветовой индикатор** статуса (OK/Warning/Critical)
- **Линейный график** временного ряда
- **Гистограмма** распределения значений
- **Обработка ошибок** с отображением

### Управление

- **Селектор интервала**: глобальное изменение временного окна
- **Автообновление**: каждые 30 секунд
- **Экспорт**: скачивание HTML-отчёта

### Обработка ошибок

- Отображение ошибок Prometheus на графиках
- Fallback на моковые данные в MOCK_MODE
- Graceful degradation при недоступности API

## 🎨 UI/UX

### Дизайн
- Современный минималистичный дизайн
- Адаптивная сетка карточек
- Консистентная цветовая схема
- Интуитивные элементы управления

### Интерактивность
- Hover-эффекты на графиках
- Анимированные переходы
- Responsive layout
- Статусные индикаторы

## 🔄 Миграция

### Изменения в существующем коде

1. **config.py**: добавлены `KPI_METRICS_CONFIG`, `TIME_INTERVALS`, `PROMETHEUS_URL`
2. **routes.py**: добавлены `/api/prometheus/query_range`, `/api/kpi/config`
3. **dashboard.html**: полностью переписан
4. **dashboard.js**: полностью переписан

### Обратная совместимость

- Существующие эндпоинты (`/data`, `/history`) сохранены
- MOCK_MODE поддерживается
- Конфигурация метрик не изменена

## 🐛 Отладка

### Логи

```python
# Включение debug-логов
print(f"[DEBUG] KPI config loaded: {len(kpiConfig)} metrics")
print(f"[DEBUG] Prometheus query: {query}")
```

### Тестирование

```bash
# Проверка API
curl -v http://localhost:5000/api/kpi/config

# Проверка Prometheus прокси
curl -v "http://localhost:5000/api/prometheus/query_range?query=test&start=1&end=2&step=1"
```

## 📈 Производительность

### Оптимизации

- Кэширование конфигурации KPI
- Параллельные запросы к Prometheus
- Ленивая загрузка графиков
- Debounced обновления

### Мониторинг

- Время ответа API
- Количество запросов к Prometheus
- Использование памяти
- Ошибки загрузки данных

## 🔮 Будущие улучшения

### Планируемые функции

1. **Фильтрация по лейблам**
   - Группировка метрик по сервисам
   - Фильтры по подам/namespace

2. **Алерты**
   - Уведомления о превышении порогов
   - Email/Slack интеграция

3. **Дашборды**
   - Сохранение пользовательских дашбордов
   - Drag-and-drop настройка

4. **Аналитика**
   - Тренды и аномалии
   - Прогнозирование

---

## ✅ Статус реализации

- [x] Backend API (Prometheus прокси)
- [x] KPI конфигурация
- [x] Frontend компоненты
- [x] Интервалы времени
- [x] Графики (линия + гистограмма)
- [x] Экспорт отчётов
- [x] Обработка ошибок
- [x] Тестирование
- [x] Документация

**Модернизация завершена! 🎉** 