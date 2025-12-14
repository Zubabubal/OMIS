"""
AnalysisAlertController из диаграммы контроллеров
C AnalysisAlertController
-alertRepo: iAlertRepo
-forecastRepo: iForecastRepo
+проверитьКритическиеЯвления(прогноз:Forecast):Alert
+разослатьОповещение(alert:Alert):void
AnalysisAlertController->(создает)Alert
iAlertRepo->(использует)AnalysisAlertController
iForecastRepo->(читает)AnalysisAlertController
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from domain.models import Alert, Прогноз, Оповещение, AlertLevel
from domain.repositories import IAlertRepo, IForecastRepo


class AnalysisAlertController:
    """
    Контроллер анализа и генерации оповещений
    C AnalysisAlertController
    """

    def __init__(self, alert_repo: IAlertRepo, forecast_repo: IForecastRepo):
        """
        Конструктор получает репозитории через DI
        -alertRepo: iAlertRepo
        -forecastRepo: iForecastRepo
        """
        self.alert_repo = alert_repo
        self.forecast_repo = forecast_repo
        self.logger = logging.getLogger(__name__)

        # Пороги для критических явлений
        self.пороги = {
            "температура": {
                "мороз": -15.0,
                "жара": 35.0,
                "сильный_мороз": -25.0,
                "сильная_жара": 40.0
            },
            "ветер": {
                "сильный": 15.0,
                "штормовой": 25.0,
                "ураганный": 33.0
            },
            "осадки": {
                "сильные": 30.0,
                "очень_сильные": 50.0,
                "экстремальные": 100.0
            }
        }

    async def проверитьКритическиеЯвления(self, прогноз: Прогноз) -> Optional[Alert]:
        """+проверитьКритическиеЯвления(прогноз:Forecast):Alert"""
        self.logger.info(f"Проверка критических явлений для прогноза {прогноз.идПрогноза}")

        критическое_явление = None
        уровень = AlertLevel.WARNING

        # Проверка температуры
        if прогноз.температура <= self.пороги["температура"]["сильный_мороз"]:
            критическое_явление = "Экстремальный мороз"
            уровень = AlertLevel.DANGER
        elif прогноз.температура <= self.пороги["температура"]["мороз"]:
            критическое_явление = "Сильный мороз"
            уровень = AlertLevel.WARNING
        elif прогноз.температура >= self.пороги["температура"]["сильная_жара"]:
            критическое_явление = "Экстремальная жара"
            уровень = AlertLevel.DANGER
        elif прогноз.температура >= self.пороги["температура"]["жара"]:
            критическое_явление = "Сильная жара"
            уровень = AlertLevel.WARNING

        # Проверка ветра
        elif прогноз.скоростьВетра and прогноз.скоростьВетра >= self.пороги["ветер"]["ураганный"]:
            критическое_явление = "Ураганный ветер"
            уровень = AlertLevel.DANGER
        elif прогноз.скоростьВетра and прогноз.скоростьВетра >= self.пороги["ветер"]["штормовой"]:
            критическое_явление = "Штормовой ветер"
            уровень = AlertLevel.WARNING

        # Проверка осадков
        elif прогноз.вероятностьОсадков >= 90:  # Вероятность осадков 90%+
            критическое_явление = "Сильные осадки"
            уровень = AlertLevel.WARNING

        if критическое_явление:
            # Создание оповещения
            alert = Alert(
                id=str(uuid.uuid4()),
                level=уровень,
                type=критическое_явление,
                region=прогноз.регион,
                valid_from=datetime.fromtimestamp(прогноз.датаСоздания / 1000),
                valid_to=datetime.fromtimestamp(прогноз.датаСоздания / 1000) + timedelta(hours=24),
                description=f"{критическое_явление} в регионе {прогноз.регион}. "
                            f"Температура: {прогноз.температура}°C, "
                            f"Ветер: {прогноз.скоростьВетра} м/с, "
                            f"Осадки: {прогноз.вероятностьОсадков}%"
            )

            # AnalysisAlertController->(создает)Alert
            self.logger.warning(f"Создано оповещение: {критическое_явление} уровень {уровень.value}")

            # Сохранение в репозиторий
            self.alert_repo.сохранить(alert)

            return alert

        return None

    async def разослатьОповещение(self, alert: Alert) -> None:
        """+разослатьОповещение(alert:Alert):void"""
        self.logger.info(f"Рассылка оповещения {alert.id} уровня {alert.level.value}")

        # Преобразование в модель Оповещение
        оповещение = alert.to_оповещение()

        # В реальной системе здесь была бы отправка по каналам:
        # - Веб-интерфейс
        # - Email
        # - SMS
        # - Мобильные уведомления

        каналы = ["веб-интерфейс", "email", "sms"]

        for канал in каналы:
            self.logger.info(f"Отправка через {канал}: {alert.description[:50]}...")

        self.logger.info(f"Оповещение {alert.id} разослано через {len(каналы)} каналов")

    async def проверитьАктуальныеПрогнозы(self) -> List[Alert]:
        """Проверка всех актуальных прогнозов на критические явления"""
        self.logger.info("Проверка всех актуальных прогнозов")

        # Получение актуальных прогнозов
        актуальные_прогнозы = self.forecast_repo.получитьАктуальные("Минск")

        оповещения = []

        for прогноз in актуальные_прогнозы:
            try:
                alert = await self.проверитьКритическиеЯвления(прогноз)
                if alert:
                    оповещения.append(alert)

                    # Рассылка оповещения
                    await self.разослатьОповещение(alert)
            except Exception as e:
                self.logger.error(f"Ошибка проверки прогноза {прогноз.идПрогноза}: {e}")

        self.logger.info(f"Найдено {len(оповещения)} критических явлений")
        return оповещения

    async def получитьСтатистикуОповещений(self) -> Dict[str, Any]:
        """Статистика оповещений"""
        все_оповещения = self.alert_repo.найтиВсе()

        статистика = {
            "всего": len(все_оповещения),
            "по_уровням": {},
            "по_типам": {},
            "последние_24ч": 0
        }

        # Подсчет по уровням и типам
        for alert in все_оповещения:
            уровень = alert.level.value
            тип = alert.type

            if уровень not in статистика["по_уровням"]:
                статистика["по_уровням"][уровень] = 0
            статистика["по_уровням"][уровень] += 1

            if тип not in статистика["по_типам"]:
                статистика["по_типам"][тип] = 0
            статистика["по_типам"][тип] += 1

            # Проверка времени создания (последние 24 часа)
            if alert.valid_from >= datetime.now() - timedelta(hours=24):
                статистика["последние_24ч"] += 1

        return статистика