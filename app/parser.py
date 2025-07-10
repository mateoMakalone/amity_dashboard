import re

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
    Безопасно вычисляет формулу для KPI-метрик, поддерживает sum(...)
    """
    def sum_expr(name):
        base_name = name.split('{')[0]
        return sum(val for key, val in metrics.items() if key.startswith(base_name + '{'))
    try:
        modified_formula = formula.replace("sum(", "sum_expr(")
        result = eval(modified_formula, {"sum_expr": sum_expr})
        if isinstance(result, float) and (result == float('inf') or result != result):
            return 0.0
        return result
    except ZeroDivisionError:
        return 0.0
    except Exception:
        return 0.0

def should_display_metric(metric_name, config):
    base_name = metric_name.split('{')[0]
    for category in config:
        for pattern in category["metrics"]:
            if re.fullmatch(pattern, base_name):
                return True
    return False
