"""
Веб-слой системы
"""

from .api_adapter import WebInterfaceAdapter
from .api_server import WeatherAPIServer

__all__ = [
    'WebInterfaceAdapter',
    'WeatherAPIServer'
]