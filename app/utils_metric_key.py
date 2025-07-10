import re

class MetricKeyHelper:
    @staticmethod
    def normalize(key: str) -> str:
        """Удаляет лишние запятые, пробелы, стандартизирует лейблы."""
        return re.sub(r',\s*}', '}', key.strip())

    @staticmethod
    def match(key: str, pattern: str) -> bool:
        """Сравнивает два ключа после нормализации."""
        return MetricKeyHelper.normalize(key) == MetricKeyHelper.normalize(pattern) 