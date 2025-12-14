"""
Адаптер для веб-интерфейса
Преобразует данные системы в формат для HTML интерфейса
"""

from typing import Dict, Any, List
from datetime import datetime

from domain.models import WeatherData, Forecast, Alert, AlertLevel


class WebInterfaceAdapter:
    """Адаптер для взаимодействия с HTML интерфейсом"""

    @staticmethod
    def prepare_weather_data(weather_data: WeatherData) -> Dict[str, Any]:
        """Подготовка данных для виджета погоды"""
        return {
            "temperature": f"{weather_data.temperature:.1f}°C",
            "pressure": f"{weather_data.pressure:.0f} мм",
            "wind": f"{weather_data.wind_direction}, {weather_data.wind_speed} м/с",
            "humidity": f"{weather_data.humidity:.0f}%",
            "phenomena": weather_data.phenomena,
            "station_id": weather_data.station_id,
            "timestamp": weather_data.timestamp.isoformat()
        }

    @staticmethod
    def prepare_forecast_chart_data(forecast: Forecast) -> Dict[str, Any]:
        """Подготовка данных для графика прогноза"""
        labels = [point["time"] for point in forecast.points[:8]]
        temperatures = [point["temperature"] for point in forecast.points[:8]]
        humidity = [point["humidity"] for point in forecast.points[:8]]

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Температура (°C)",
                    "data": temperatures,
                    "borderColor": "#3b82f6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)"
                },
                {
                    "label": "Влажность (%)",
                    "data": humidity,
                    "borderColor": "#10b981",
                    "borderDash": [5, 5]
                }
            ]
        }

    @staticmethod
    def prepare_alerts_data(alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Подготовка данных оповещений"""
        prepared = []
        for alert in alerts:
            if alert.level == AlertLevel.DANGER:
                border_color = "#ef4444"
                bg_color = "rgba(239, 68, 68, 0.1)"
                icon = "fa-bolt"
                level_text = "КРАСНЫЙ"
            elif alert.level == AlertLevel.WARNING:
                border_color = "#f59e0b"
                bg_color = "rgba(245, 158, 11, 0.1)"
                icon = "fa-cloud-fog"
                level_text = "ОРАНЖЕВЫЙ"
            elif alert.level == AlertLevel.CRITICAL:
                border_color = "#dc2626"
                bg_color = "rgba(220, 38, 38, 0.1)"
                icon = "fa-triangle-exclamation"
                level_text = "КРИТИЧЕСКИЙ"
            else:
                continue

            prepared.append({
                "id": alert.id,
                "level": level_text,
                "type": alert.type,
                "region": alert.region,
                "description": alert.description,
                "valid_from": alert.valid_from.strftime("%d.%m.%Y %H:%M"),
                "valid_to": alert.valid_to.strftime("%d.%m.%Y %H:%M"),
                "border_color": border_color,
                "bg_color": bg_color,
                "icon": icon,
                "is_active": alert.is_active
            })

        return prepared

    @staticmethod
    def prepare_archive_data(weather_data_list: List[WeatherData]) -> List[Dict[str, Any]]:
        """Подготовка данных для архива"""
        prepared = []

        for data in weather_data_list:
            # Определение статуса
            if data.temperature > 30 or data.temperature < -20:
                status_tag = "tag-crit"
                status_text = "Опасно"
            elif data.temperature > 25 or data.temperature < -10:
                status_tag = "tag-warn"
                status_text = "Внимание"
            else:
                status_tag = "tag-ok"
                status_text = "Норма"

            # Определение иконки явлений
            if "гроза" in data.phenomena.lower():
                icon = "fa-cloud-bolt"
            elif "дождь" in data.phenomena.lower():
                icon = "fa-cloud-rain"
            elif "снег" in data.phenomena.lower():
                icon = "fa-snowflake"
            elif "облачно" in data.phenomena.lower():
                icon = "fa-cloud"
            elif "солнце" in data.phenomena.lower() or "ясно" in data.phenomena.lower():
                icon = "fa-sun"
            else:
                icon = "fa-cloud-sun"

            prepared.append({
                "timestamp": data.timestamp.strftime("%d.%m.%Y %H:%M"),
                "temperature": f"{data.temperature:.1f}°C",
                "humidity": f"{data.humidity:.0f}%",
                "pressure": f"{data.pressure:.0f} мм",
                "wind": f"{data.wind_direction}, {data.wind_speed} м/с",
                "phenomena_icon": icon,
                "phenomena_text": data.phenomena,
                "status_tag": status_tag,
                "status_text": status_text
            })

        return prepared

    @staticmethod
    def prepare_modeling_parameters() -> Dict[str, Any]:
        """Подготовка параметров моделирования"""
        return {
            "algorithms": [
                {"value": "WRF-ARW (Mesoscale)", "label": "WRF-ARW (Mesoscale)"},
                {"value": "GFS (Global)", "label": "GFS (Global)"},
                {"value": "ICON-EU", "label": "ICON-EU"}
            ],
            "initial_conditions": [
                {"value": "Текущие (Real-time)", "label": "Текущие (Real-time)"},
                {"value": "Архив (12.05.2024)", "label": "Архив (12.05.2024)"}
            ],
            "grid_resolutions": [
                {"value": "3 км (Высокое)", "label": "3 км (Высокое)"},
                {"value": "9 км (Среднее)", "label": "9 км (Среднее)"},
                {"value": "27 км (Низкое)", "label": "27 км (Низкое)"}
            ]
        }

    @staticmethod
    def prepare_alert_types() -> List[Dict[str, Any]]:
        """Подготовка типов оповещений"""
        return [
            {"value": "Гроза / Молния", "label": "Гроза / Молния"},
            {"value": "Шквалистый ветер", "label": "Шквалистый ветер"},
            {"value": "Град", "label": "Град"},
            {"value": "Гололедица", "label": "Гололедица"},
            {"value": "Туман", "label": "Туман"},
            {"value": "Сильный мороз", "label": "Сильный мороз"},
            {"value": "Сильная жара", "label": "Сильная жара"}
        ]

    @staticmethod
    def prepare_regions() -> List[Dict[str, Any]]:
        """Подготовка списка регионов"""
        return [
            {"value": "г. Минск (Все районы)", "label": "г. Минск (Все районы)"},
            {"value": "Минская область (Север)", "label": "Минская область (Север)"},
            {"value": "Минская область (Юг)", "label": "Минская область (Юг)"},
            {"value": "МКАД", "label": "МКАД"},
            {"value": "Брестская область", "label": "Брестская область"},
            {"value": "Гомельская область", "label": "Гомельская область"},
            {"value": "Витебская область", "label": "Витебская область"}
        ]