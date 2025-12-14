"""
Слой представления (View Layer)
"""

from .interfaces import (
    ОсновнойИнтерфейс,
    ПрогнозView,
    АнализView,
    IMonitoringView,
    IModelingView,
    IArchiveView,
    IAlertsView
)

from .meteorologist_panel import ПанельМетеоролога
from .climatologist_panel import ПанельКлиматолога

__all__ = [
    'ОсновнойИнтерфейс',
    'ПрогнозView',
    'АнализView',
    'IMonitoringView',
    'IModelingView',
    'IArchiveView',
    'IAlertsView',
    'ПанельМетеоролога',
    'ПанельКлиматолога'
]