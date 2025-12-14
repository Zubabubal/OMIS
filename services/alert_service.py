"""
Сервис оповещений
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid

from domain.models import Alert, AlertLevel, WeatherData
from domain.repositories import WeatherDataRepository, AlertRepository


class AlertService:
    """Сервис оповещений"""

    def __init__(self, data_repo: WeatherDataRepository, alert_repo: AlertRepository):
        self.data_repo = data_repo
        self.alert_repo = alert_repo
        self.thresholds = {
            "wind_speed": 20.0,
            "temperature_low": -25.0,
            "temperature_high": 35.0,
            "precipitation": 50.0
        }

    async def check_alerts(self, station_id: str) -> List[Alert]:
        """Проверка условий для генерации оповещений"""
        latest_data = await self.data_repo.get_latest_by_station(station_id)
        if not latest_data:
            return []

        alerts = []
        now = datetime.now()

        # Проверка скорости ветра
        if latest_data.wind_speed >= self.thresholds["wind_speed"]:
            alert = Alert(
                id=str(uuid.uuid4()),
                level=AlertLevel.DANGER,
                type="Шквалистый ветер",
                region=f"Станция {station_id}",
                valid_from=now,
                valid_to=now + timedelta(hours=3),
                description=f"Шквалистый ветер до {latest_data.wind_speed} м/с"
            )
            alerts.append(alert)

        # Проверка температуры
        if latest_data.temperature <= self.thresholds["temperature_low"]:
            alert = Alert(
                id=str(uuid.uuid4()),
                level=AlertLevel.WARNING,
                type="Сильный мороз",
                region=f"Станция {station_id}",
                valid_from=now,
                valid_to=now + timedelta(hours=12),
                description=f"Температура опустилась до {latest_data.temperature}°C"
            )
            alerts.append(alert)
        elif latest_data.temperature >= self.thresholds["temperature_high"]:
            alert = Alert(
                id=str(uuid.uuid4()),
                level=AlertLevel.WARNING,
                type="Сильная жара",
                region=f"Станция {station_id}",
                valid_from=now,
                valid_to=now + timedelta(hours=12),
                description=f"Температура поднялась до {latest_data.temperature}°C"
            )
            alerts.append(alert)

        # Проверка осадков
        if latest_data.precipitation >= self.thresholds["precipitation"]:
            alert = Alert(
                id=str(uuid.uuid4()),
                level=AlertLevel.WARNING,
                type="Сильные осадки",
                region=f"Станция {station_id}",
                valid_from=now,
                valid_to=now + timedelta(hours=6),
                description=f"Интенсивность осадков {latest_data.precipitation} мм/час"
            )
            alerts.append(alert)

        # Сохранение оповещений
        for alert in alerts:
            await self.alert_repo.save(alert)

        return alerts

    async def check_trend_alerts(self, station_id: str, hours: int = 24) -> List[Alert]:
        """Проверка трендов для генерации оповещений"""
        history = await self.data_repo.get_station_history(station_id, hours)
        if len(history) < 2:
            return []

        # Анализ трендов
        temperatures = [data.temperature for data in history]
        pressures = [data.pressure for data in history]

        # Проверка быстрого падения давления (признак ухудшения погоды)
        if len(pressures) >= 3:
            pressure_change = pressures[-1] - pressures[0]
            if pressure_change < -10:  # Падение более 10 гПа за период
                alert = Alert(
                    id=str(uuid.uuid4()),
                    level=AlertLevel.WARNING,
                    type="Быстрое падение давления",
                    region=f"Станция {station_id}",
                    valid_from=datetime.now(),
                    valid_to=datetime.now() + timedelta(hours=6),
                    description=f"Давление упало на {abs(pressure_change):.1f} гПа за {hours} часов"
                )
                await self.alert_repo.save(alert)
                return [alert]

        return []