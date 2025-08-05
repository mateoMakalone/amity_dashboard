import re
from app.utils_metric_key import MetricKeyHelper

def normalize_metric_name(name, labels):
    # Сортировка лейблов для консистентности
    if not labels:
        return name
    sorted_labels = sorted(labels.items())
    label_str = ','.join(f'{k}="{v}"' for k, v in sorted_labels)
    return f'{name}{{{label_str}}}'

def find_metric_value(metrics, metric_name):
    """
    Ищет значение метрики в словаре метрик
    Поддерживает поиск по точному имени и по базовому имени без лейблов
    """
    # Прямой поиск
    if metric_name in metrics:
        return metrics[metric_name]
    
    # Поиск по базовому имени (без лейблов)
    base_name = metric_name.split('{')[0]
    if base_name in metrics:
        return metrics[base_name]
    
    # Поиск метрик с лейблами, начинающихся с базового имени
    for key, value in metrics.items():
        if key.startswith(base_name + '{'):
            return value
    
    # Поиск по базовому имени в ключах с лейблами
    for key, value in metrics.items():
        if '{' in key and key.split('{')[0] == base_name:
            return value
    
    return None

def parse_metrics(text):
    metrics = {}
    current_metric = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("# HELP"):
            continue
        if line.startswith("# TYPE"):
            current_metric = line.split()[2]
            continue
        if current_metric:
            try:
                if '{' in line:
                    name_part, value_part = line.split('}', 1)
                    name = name_part + '}'
                    value = float(value_part.strip())
                    # Парсим лейблы
                    base = name.split('{')[0].strip()
                    label_str = name[name.find('{')+1:name.find('}')]
                    labels = dict(pair.split('=') for pair in label_str.split(',') if '=' in pair)
                    labels = {k.strip(): v.strip().strip('"') for k, v in labels.items()}
                    norm_key = normalize_metric_name(base, labels)
                    metrics[norm_key] = value
                    metrics[base] = value
                else:
                    name, value = line.rsplit(' ', 1)
                    value = float(value)
                    metrics[name] = value
            except ValueError:
                continue
    return metrics

def filter_metric(metrics, base, labels=None):
    """
    Возвращает значение метрики с нужными лейблами (или None, если не найдено)
    labels: dict, например {"database": "db01"}
    """
    if labels is None:
        labels = {}
    for k, v in metrics.items():
        if not k.startswith(base):
            continue
        if '{' in k:
            label_str = k[k.find('{')+1:k.find('}')]
            label_pairs = dict(
                pair.split('=') for pair in label_str.split(',') if pair and '=' in pair
            )
            # Убираем кавычки
            label_pairs = {kk: vv.strip('"') for kk, vv in label_pairs.items()}
            if all(label_pairs.get(lk) == lv for lk, lv in labels.items()):
                return v
        else:
            if not labels:
                return v
    return None

def sum_metric(metrics, base, labels=None):
    """
    Суммирует значения метрик с нужным base и лейблами (если labels=None, то все)
    """
    total = 0.0
    found = False
    for k, v in metrics.items():
        if not k.startswith(base):
            continue
        if labels:
            if '{' in k:
                label_str = k[k.find('{')+1:k.find('}')]
                label_pairs = dict(
                    pair.split('=') for pair in label_str.split(',') if pair and '=' in pair
                )
                label_pairs = {kk: vv.strip('"') for kk, vv in label_pairs.items()}
                if all(label_pairs.get(lk) == lv for lk, lv in labels.items()):
                    total += v
                    found = True
            # else: не совпадает
        else:
            total += v
            found = True
    return total if found else None

def get_metric(metrics, name):
    if name in metrics:
        return metrics[name]
    for key in metrics:
        if key.startswith(name + "{"):
            return metrics[key]
    return 0

def eval_formula(formula, metrics):
    """
    Безопасно вычисляет формулу для KPI-метрик, поддерживает sum(...), rate(...), avg(...) с лейблами
    """
    def sum_expr(name):
        # Извлекаем базовое имя и лейблы из строки вида "metric_name{label1=\"value1\",label2=\"value2\"}"
        if '{' in name:
            base_name = name.split('{')[0]
            label_str = name[name.find('{')+1:name.find('}')]
            # Парсим лейблы
            labels = {}
            for pair in label_str.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    labels[key.strip()] = value.strip().strip('"')
            
            # Ищем метрики с подходящими лейблами
            total = 0.0
            found = False
            for key, val in metrics.items():
                if not key.startswith(base_name + '{'):
                    continue
                # Проверяем лейблы
                if '{' in key:
                    key_label_str = key[key.find('{')+1:key.find('}')]
                    key_labels = {}
                    for pair in key_label_str.split(','):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            key_labels[k.strip()] = v.strip().strip('"')
                    
                    # Проверяем, что все требуемые лейблы совпадают
                    if all(key_labels.get(lk) == lv for lk, lv in labels.items()):
                        total += val
                        found = True
            return total if found else 0.0
        else:
            # Простая сумма без лейблов
            return sum(val for key, val in metrics.items() if key.startswith(name + '{'))
    
    def rate_expr(name):
        # Для rate() просто возвращаем текущее значение (упрощенная реализация)
        # В реальности rate() требует историю значений
        return sum_expr(name)
    
    def avg_expr(name):
        # Для avg() возвращаем среднее значение
        values = []
        if '{' in name:
            base_name = name.split('{')[0]
            label_str = name[name.find('{')+1:name.find('}')]
            labels = {}
            for pair in label_str.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    labels[key.strip()] = value.strip().strip('"')
            
            for key, val in metrics.items():
                if not key.startswith(base_name + '{'):
                    continue
                if '{' in key:
                    key_label_str = key[key.find('{')+1:key.find('}')]
                    key_labels = {}
                    for pair in key_label_str.split(','):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            key_labels[k.strip()] = v.strip().strip('"')
                    
                    if all(key_labels.get(lk) == lv for lk, lv in labels.items()):
                        values.append(val)
        else:
            values = [val for key, val in metrics.items() if key.startswith(name + '{')]
        
        return sum(values) / len(values) if values else 0.0
    
    try:
        # Если формула - это просто имя метрики без функций, используем find_metric_value
        if not any(func in formula for func in ["sum(", "rate(", "avg(", "+", "-", "*", "/", "("]):
            return find_metric_value(metrics, formula) or 0.0
        
        # Обрабатываем сложные формулы с лейблами
        # Пример: jvm_memory_used_bytes{area="heap",id="Tenured Gen"} / 1024 / 1024
        if "{" in formula and "}" in formula:
            # Извлекаем метрику с лейблами
            metric_part = formula.split("}")[0] + "}"
            operation_part = formula.split("}")[1].strip()
            
            # Находим значение метрики
            metric_value = find_metric_value(metrics, metric_part)
            if metric_value is None:
                return 0.0
            
            # Применяем операции
            if operation_part:
                try:
                    # Создаем безопасный контекст для операций
                    safe_dict = {"__builtins__": {}, "metric_value": metric_value}
                    result = eval(f"metric_value{operation_part}", safe_dict)
                    return result if isinstance(result, (int, float)) else 0.0
                except:
                    return 0.0
            else:
                return metric_value
        
        # Обрабатываем формулы с функциями rate() и avg()
        if "rate(" in formula or "avg(" in formula:
            # Упрощенная обработка - извлекаем метрику из функции
            if "rate(" in formula:
                # rate(metric_name{labels}[1m]) -> metric_name{labels}
                start = formula.find("rate(") + 5
                end = formula.find("[1m]")
                if end == -1:
                    end = formula.find(")")
                metric_name = formula[start:end]
                return find_metric_value(metrics, metric_name) or 0.0
            
            elif "avg(" in formula:
                # avg(rate(...)) -> извлекаем внутреннюю метрику
                if "rate(" in formula:
                    start = formula.find("rate(") + 5
                    end = formula.find("[1m]")
                    if end == -1:
                        end = formula.find(")")
                    metric_name = formula[start:end]
                    return find_metric_value(metrics, metric_name) or 0.0
                else:
                    # avg(metric_name) -> metric_name
                    start = formula.find("avg(") + 4
                    end = formula.find(")")
                    metric_name = formula[start:end]
                    return find_metric_value(metrics, metric_name) or 0.0
        
        # Заменяем функции на наши реализации для остальных случаев
        modified_formula = formula.replace("sum(", "sum_expr(")
        modified_formula = modified_formula.replace("rate(", "rate_expr(")
        modified_formula = modified_formula.replace("avg(", "avg_expr(")
        
        # Создаем безопасный контекст для eval
        safe_dict = {
            "sum_expr": sum_expr,
            "rate_expr": rate_expr,
            "avg_expr": avg_expr,
            "__builtins__": {}
        }
        
        # Добавляем все метрики в контекст
        for key, value in metrics.items():
            safe_dict[key] = value
        
        result = eval(modified_formula, safe_dict)
        
        if isinstance(result, float) and (result == float('inf') or result != result):
            return 0.0
        return result
    except ZeroDivisionError:
        return 0.0
    except Exception as e:
        print(f"[DEBUG] eval_formula error for '{formula}': {e}")
        return 0.0

def should_display_metric(metric_name, config):
    base_name = metric_name.split('{')[0]
    for category in config:
        for pattern in category["metrics"]:
            if re.fullmatch(pattern, base_name):
                return True
    return False

def parse_prometheus_text(text):
    result = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.strip().split(" ")
        if len(parts) == 2:
            key, val = parts
            try:
                result[key] = float(val)
            except ValueError:
                continue
    return result
