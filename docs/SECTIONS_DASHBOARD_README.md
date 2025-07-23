# 🚀 Модернизированный Amity Metrics Dashboard

## 📋 Обзор

Полностью переписанный и отлаженный дашборд отображения метрик с новой архитектурой:

- ✅ **Секции метрик** - группировка по категориям (KPI, PostgreSQL, JVM, Jetty, System)
- ✅ **Исторические графики** - построение по запросам к Prometheus
- ✅ **Гибкая визуализация** - линии, гистограммы, тайм-серии
- ✅ **Debug-режим** - отображение всех доступных метрик с диагностикой
- ✅ **Экспорт отчётов** - standalone HTML с интерактивными графиками

## 🏗️ Архитектура

### Backend (Flask)

```
app/
├── config.py              # SECTIONS, ALL_METRICS, TIME_INTERVALS
├── routes.py              # Новые API эндпоинты
├── metrics.py             # Существующая логика метрик
└── templates/
    └── dashboard.html     # Модернизированный шаблон с секциями
```

### Frontend (Vanilla JS + Plotly.js)

```
app/static/js/
└── dashboard.js           # Новая архитектура с секциями и debug-режимом
```

## 🔧 Конфигурация

### Секции метрик (`config.py`)

```python
SECTIONS = {
    "KPI": [
        "avg_response_time_api",
        "system_cpu_usage", 
        "jvm_memory_used",
        "postgres_connections",
        "postgres_locks",
        "gc_pause_time",
        "system_load",
        "tx_pool_size"
    ],
    "Transactions": [
        "postgres_transactions_total",
        "postgres_rows_inserted_total",
        "postgres_rows_updated_total",
        "postgres_rows_deleted_total"
    ],
    "PostgreSQL": [
        "postgres_connections",
        "postgres_locks",
        "postgres_blocks_reads_total",
        "postgres_rows_inserted_total",
        "postgres_rows_updated_total",
        "postgres_transactions_total"
    ],
    "JVM": [
        "gc_pause_time",
        "jvm_memory_used",
        "jvm_threads_live_threads",
        "jvm_classes_loaded_classes"
    ],
    "Jetty": [
        "jetty_server_requests_seconds_avg",
        "jetty_get_avg_time",
        "jetty_post_avg_time",
        "jetty_connections_current_connections",
        "jetty_connections_bytes_in_bytes_sum",
        "jetty_connections_bytes_out_bytes_sum"
    ],
    "System": [
        "system_cpu_usage",
        "system_load",
        "system_cpu_count"
    ]
}
```

### Конфигурация метрик

```python
ALL_METRICS = {
    "avg_response_time_api": {
        "label": "Среднее время ответа API",
        "promql": 'avg(rate(jetty_server_requests_seconds_sum{outcome="SUCCESS",status="200"}[1m])) / avg(rate(jetty_server_requests_seconds_count{outcome="SUCCESS",status="200"}[1m]))',
        "type": "trend+bar",  # trend, bar, or both
        "unit": "сек",
        "color": "#e74c3c",
        "format": "fixed3",
        "thresholds": {"warning": 0.5, "critical": 1.0}
    },
    # ... другие метрики
}
```

## 🚀 API Эндпоинты

### Новые эндпоинты

- `GET /api/sections` - конфигурация всех секций и метрик
- `GET /api/sections/{section_name}/metrics` - метрики конкретной секции
- `GET /api/metrics/{metric_id}/history` - история конкретной метрики
- `GET /api/prometheus/query_range` - прокси к Prometheus API

### Существующие (для обратной совместимости)

- `GET /data` - текущие значения метрик
- `GET /history` - история метрик
- `GET /api/kpi/config` - конфигурация KPI

## 💻 Frontend

### Отображение по секциям

- **Секции**: KPI, Transactions, PostgreSQL, JVM, Jetty, System
- **Сворачивание/разворачивание**: клик по заголовку секции
- **Визуальное выделение**: заголовки, отступы, фон
- **Адаптивная сетка**: автоматическое размещение карточек

### Гибкая визуализация

Каждая метрика может отображаться как:

- **Линия по времени** (`type: "trend"`) - временные ряды
- **Гистограмма** (`type: "bar"`) - распределение значений
- **Оба типа** (`type: "trend+bar"`) - линия + гистограмма

### Выбор временного диапазона

- **Глобальный dropdown**: 15 / 30 / 45 / 60 минут
- **Синхронизация**: все графики обновляются одновременно
- **Перезапрос**: автоматическое обновление через Prometheus API

### Экспорт отчётов

- **Кнопка**: "📤 Экспорт отчёта"
- **Формат**: Standalone HTML с Plotly.js
- **Содержимое**: все метрики текущего диапазона
- **Интерактивность**: графики работают без интернета

## 🧪 Debug Mode

### Активация

- **URL параметр**: `?debug=true`
- **Переключатель**: кнопка "🐛 Debug" на странице
- **Состояние**: сохраняется в URL

### Отображаемая информация

- **JSON-ответ Prometheus**: полный ответ API
- **Статистика**: количество точек, min/max значения
- **Диагностика**: пустые ряды, ошибки запросов
- **Подсветка**: метрики с N/A значениями

### Пример debug-информации

```
Debug Info:
JSON: {"status": "success", "data": {...}}
Stats: min: 0.03, max: 3.42, count: 60
```

## 🎨 UI/UX

### Дизайн секций

```
=== Key Performance Indicators ===
[график] Среднее время ответа API
[график] Загрузка CPU
...

=== JVM ===
[график] Время паузы GC
[график] Память JVM
...

=== PostgreSQL ===
[график] Активные подключения
[график] Вставки в БД
...
```

### Интерактивность

- **Hover-эффекты**: подсказки на графиках
- **Анимации**: плавные переходы при сворачивании
- **Responsive**: адаптация под размер экрана
- **Статусные индикаторы**: OK/Warning/Critical

## 🔄 Миграция

### Изменения в существующем коде

1. **config.py**: добавлены `SECTIONS`, `ALL_METRICS`
2. **routes.py**: добавлены новые API эндпоинты
3. **dashboard.html**: полностью переписан с секциями
4. **dashboard.js**: новая архитектура с секциями

### Обратная совместимость

- ✅ Существующие эндпоинты сохранены
- ✅ MOCK_MODE поддерживается
- ✅ Конфигурация метрик не изменена
- ✅ Старые дашборды продолжают работать

## 🚀 Запуск и тестирование

### Запуск

```bash
python run.py
```

### Доступ

- **Главная страница**: http://localhost:5000/
- **Debug-режим**: http://localhost:5000/?debug=true
- **API секций**: http://localhost:5000/api/sections
- **API метрики**: http://localhost:5000/api/metrics/system_cpu_usage/history

### Тестирование

```bash
python test_sections_dashboard.py
```

## 📊 Функциональность

### Секции метрик

- **KPI**: ключевые показатели производительности
- **Transactions**: транзакции базы данных
- **PostgreSQL**: метрики PostgreSQL
- **JVM**: метрики Java Virtual Machine
- **Jetty**: метрики веб-сервера
- **System**: системные метрики

### Типы визуализации

- **trend**: линейные графики временных рядов
- **bar**: гистограммы распределения значений
- **trend+bar**: комбинация обоих типов

### Обработка ошибок

- **Отображение ошибок**: на графиках и в debug-режиме
- **Graceful degradation**: fallback при недоступности API
- **Логирование**: детальные логи в dev-режиме

## 🐛 Отладка

### Логи

```python
print(f"[DEBUG] Sections loaded: {len(sections)}")
print(f"[DEBUG] Metric history: {metric_id}")
```

### Тестирование API

```bash
# Конфигурация секций
curl http://localhost:5000/api/sections

# История метрики
curl "http://localhost:5000/api/metrics/system_cpu_usage/history?interval=30"

# Debug-режим
curl "http://localhost:5000/?debug=true"
```

## 📈 Производительность

### Оптимизации

- **Параллельные запросы**: к Prometheus для разных метрик
- **Кэширование**: конфигурации секций
- **Ленивая загрузка**: графиков по требованию
- **Debounced обновления**: предотвращение перегрузки

### Мониторинг

- **Время ответа API**: для каждого эндпоинта
- **Количество запросов**: к Prometheus
- **Использование памяти**: для графиков
- **Ошибки загрузки**: детальная статистика

## 🔮 Будущие улучшения

### Планируемые функции

1. **Фильтрация по лейблам**
   - Группировка метрик по сервисам
   - Фильтры по подам/namespace

2. **Алерты**
   - Уведомления о превышении порогов
   - Email/Slack интеграция

3. **Дашборды**
   - Сохранение пользовательских настроек
   - Drag-and-drop настройка

4. **Аналитика**
   - Тренды и аномалии
   - Прогнозирование

---

## ✅ Статус реализации

- [x] Секции метрик (группировка по категориям)
- [x] Конфигурация ALL_METRICS с типами визуализации
- [x] Прокси эндпоинт к Prometheus
- [x] Отображение по секциям с сворачиванием
- [x] Гибкая визуализация (trend + bar)
- [x] Выбор временного диапазона
- [x] Debug-режим с детальной информацией
- [x] Экспорт отчётов в HTML
- [x] Обработка ошибок
- [x] Обратная совместимость
- [x] Тестирование
- [x] Документация

**Модернизация завершена! 🎉**

### Результат

Современный, интерактивный дашборд с:
- 6 секциями метрик
- 25+ настраиваемыми метриками
- Гибкой визуализацией
- Debug-режимом
- Экспортом отчётов
- Полной обратной совместимостью

**Дашборд готов к использованию! 🚀** 