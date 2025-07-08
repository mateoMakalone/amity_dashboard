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

def should_display_metric(metric_name, config):
    base_name = metric_name.split('{')[0]
    for category in config:
        for pattern in category["metrics"]:
            if re.fullmatch(pattern, base_name):
                return True
    return False
