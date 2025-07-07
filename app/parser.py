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

def should_display_metric(metric_name, config):
    from .config import IGNORE_METRICS
    base_name = metric_name.split('{')[0]
    if base_name in IGNORE_METRICS:
        return False
    for category in config:
        for pattern in category["metrics"]:
            if re.fullmatch(pattern, base_name):
                return True
    return False
