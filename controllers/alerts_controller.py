"""
AlertsAlertController из диаграммы контроллеров
C АльвузыAlertController (вероятно AlertsAlertController)
alertRepo: AlertRepository
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid

from domain.models import Alert, AlertLevel
from domain.repositories import AlertRepository
from services.alert_service import AlertService


class AlertsAlertController:
    """Контроллер управления оповещениями"""

    def __init__(self, alert_service: AlertService,
                 alert_repository: AlertRepository):
        self.alert_service = alert_service
        self.alert_repository = alert_repository
        self.logger = logging.getLogger(__name__)

    async def проверитьИСгенерироватьОповещения(self, station_id: str) -> List[Alert]:
        """Проверка и генерация оповещений для станции"""
        self.logger.info(f"Проверка оповещений для станции {station_id}")

        alerts = await self.alert_service.check_alerts(station_id)

        if alerts:
            self.logger.warning(f"Сгенерировано {len(alerts)} оповещений")

        return alerts

    async def получитьАктивныеОповещения(self) -> List[Dict[str, Any]]:
        """Получение активных оповещений"""
        alerts = await self.alert_repository.get_active_alerts()

        result = []
        for alert in alerts:
            result.append({
                "id": alert.id,
                "level": alert.level.value,
                "type": alert.type,
                "region": alert.region,
                "description": alert.description,
                "valid_from": alert.valid_from.isoformat(),
                "valid_to": alert.valid_to.isoformat(),
                "is_active": alert.is_active
            })

        return result

    async def создатьРучноеОповещение(self, alert_data: Dict[str, Any]) -> Alert:
        """Создание ручного оповещения"""
        alert = Alert(
            id=str(uuid.uuid4()),
            level=AlertLevel(alert_data.get("level", "warning")),
            type=alert_data.get("type", "Гроза / Молния"),
            region=alert_data.get("region", "г. Минск (Все районы)"),
            valid_from=datetime.fromisoformat(
                alert_data.get("valid_from", datetime.now().isoformat())
            ),
            valid_to=datetime.fromisoformat(
                alert_data.get("valid_to",
                               (datetime.now() + timedelta(hours=3)).isoformat())
            ),
            description=alert_data.get("description", "")
        )

        await self.alert_repository.save(alert)
        self.logger.warning(f"Создано ручное оповещение: {alert.type}")

        return alert

    async def деактивироватьОповещение(self, alert_id: str) -> bool:
        """Деактивация оповещения"""
        alert = await self.alert_repository.get_by_id(alert_id)

        if alert:
            alert.is_active = False
            await self.alert_repository.save(alert)
            return True

        return False

    async def получитьСтатистикуОповещений(self) -> Dict[str, Any]:
        """Статистика оповещений"""
        all_alerts = await self.alert_repository.get_all()
        active_alerts = await self.alert_repository.get_active_alerts()

        by_level = {}
        for level in AlertLevel:
            by_level[level.value] = len([
                a for a in all_alerts if a.level == level
            ])

        return {
            "total_alerts": len(all_alerts),
            "active_alerts": len(active_alerts),
            "alerts_by_level": by_level,
            "latest_alert": max(
                all_alerts,
                key=lambda x: x.valid_from
            ).valid_from.isoformat() if all_alerts else None
        }