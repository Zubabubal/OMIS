"""
Configuration_Manager из диаграммы
C Configuration_Manager
+загрузитьНастройки(): Properties
Configuration_Manager->(настраивает)DI_Container
"""

import json
import os
from typing import Dict, Any


class ConfigurationManager:
    """Менеджер конфигурации системы"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file

    def загрузитьНастройки(self) -> Dict[str, Any]:
        """+загрузитьНастройки(): Properties"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"Конфигурация загружена из {self.config_file}")
                    return config
            else:
                print(f"Файл конфигурации {self.config_file} не найден. Используются настройки по умолчанию.")
                return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Ошибка чтения конфигурации: {e}. Используются настройки по умолчанию.")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Конфигурация по умолчанию"""
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "weather_db",
                "user": "weather_user",
                "password": "weather_pass"
            },
            "services": {
                "data_ingestion_interval": 300,
                "forecast_update_interval": 3600,
                "alert_check_interval": 60,
                "api_port": 8000,
                "api_host": "0.0.0.0"
            },
            "models": {
                "default": "WRF-ARW",
                "available": ["WRF-ARW", "GFS", "ICON-EU", "ECMWF"],
                "ensemble_size": 5
            },
            "stations": {
                "default": "26850",
                "locations": {
                    "26850": {
                        "name": "Минск-Уручье",
                        "lat": 53.94,
                        "lon": 27.69,
                        "type": "meteo"
                    }
                }
            },
            "alerts": {
                "thresholds": {
                    "temperature_high": 35.0,
                    "temperature_low": -25.0,
                    "wind_speed": 20.0,
                    "precipitation_hourly": 50.0
                }
            }
        }

    def get(self, key: str, default=None) -> Any:
        """Получить значение конфигурации по ключу"""
        config = self.загрузитьНастройки()
        keys = key.split('.')
        value = config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, {})
            else:
                return default

        return value if value != {} else default