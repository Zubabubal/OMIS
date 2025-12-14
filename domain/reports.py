"""
Классы отчетов системы
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass
class Report:
    """Базовый класс отчета"""
    тип: str
    параметры: Dict[str, Any]
    данных: int
    временной_диапазон: Dict[str, str]
    метрики: Dict[str, Any] = field(default_factory=dict)
    сгенерирован: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class КлиматическийОтчет:
    """Климатический отчет"""
    период: str
    данных: int
    временной_диапазон: Dict[str, str] = field(default_factory=dict)
    анализ: Dict[str, Any] = field(default_factory=dict)
    рекомендации: List[str] = field(default_factory=list)
    сообщение: str = ""
    сгенерирован: str = field(default_factory=lambda: datetime.now().isoformat())