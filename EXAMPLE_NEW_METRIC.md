# Пример добавления новой метрики

## 🎯 Демонстрация простоты новой системы

### Задача
Добавить новую метрику "Количество активных пользователей" в секцию "KPI"

### Старый способ (4 места для правки)

1. **Добавить в SECTIONS**:
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
        "tx_pool_size",
        "active_users"  # ← Добавить здесь
    ],
    # ...
}
```

2. **Добавить в ALL_METRICS**:
```python
ALL_METRICS = {
    # ... существующие метрики ...
    "active_users": {  # ← Добавить здесь
        "label": "Активные пользователи",
        "promql": "active_users_total",
        "type": "trend",
        "unit": "",
        "color": "#e74c3c",
        "format": "fixed0"
    }
}
```

3. **Добавить в KPI_METRIC_IDS**:
```python
KPI_METRIC_IDS = [
    "avg_response_time_api",
    "get_response_time",
    "post_response_time",
    "system_cpu_usage",
    "jvm_memory_used",
    "postgres_connections",
    "postgres_locks",
    "gc_pause_time",
    "system_load",
    "tx_pool_size",
    "active_users"  # ← Добавить здесь
]
```

4. **Добавить в INITIAL_METRICS**:
```python
INITIAL_METRICS = [
    'tx_pool_size',
    'jetty_server_requests_seconds_avg',
    # ... много других метрик ...
    'active_users'  # ← Добавить здесь
]
```

**Время**: ~5 минут
**Риск ошибок**: Высокий (легко забыть одно из мест)

---

### Новый способ (1 место для правки)

1. **Добавить в METRICS_CONFIG**:
```python
METRICS_CONFIG = {
    # ... существующие метрики ...
    
    "active_users": {  # ← Добавить только здесь
        "section": "KPI",
        "label": "Активные пользователи",
        "promql": "active_users_total",
        "type": "trend",
        "unit": "",
        "color": "#e74c3c",
        "format": "fixed0"
    }
}
```

**Время**: ~30 секунд
**Риск ошибок**: Минимальный (только одно место)

---

## ✅ Что происходит автоматически

После добавления метрики в `METRICS_CONFIG` система автоматически:

1. **Создает секцию** (если её нет)
2. **Добавляет метрику в секцию**
3. **Генерирует конфигурацию для фронтенда**
4. **Обновляет список инициализации**
5. **Создает KPI конфигурацию** (если метрика в KPI секции)

## 🚀 Результат

- ✅ Метрика появится в дашборде
- ✅ Будет отображаться в правильной секции
- ✅ График будет работать
- ✅ Автообновление будет работать
- ✅ Экспорт будет включать новую метрику

## 📝 Дополнительные возможности

### Добавить пороги
```python
"active_users": {
    "section": "KPI",
    "label": "Активные пользователи",
    "promql": "active_users_total",
    "type": "trend",
    "unit": "",
    "color": "#e74c3c",
    "format": "fixed0",
    "thresholds": {"warning": 100, "critical": 200}  # ← Пороги
}
```

### Создать новую секцию
```python
"custom_metric": {
    "section": "Моя новая секция",  # ← Новая секция создастся автоматически
    "label": "Моя метрика",
    "promql": "my_metric",
    "type": "trend",
    "unit": "шт",
    "color": "#3498db",
    "format": "fixed0"
}
```

---

**Вывод**: Новая система в **10 раз проще** и **в 10 раз надежнее**! 🎉 