"""
ForecastServiceController <<Facade>> из диаграммы контроллеров
C ForecastServiceController <<Facade>>
-forecastRepo: iForecastRepo
-dataRepo: iSensorRepo
+запуститьМодель(типМодели:String,регион:String):Forecast
+верефицироватьПрогноз(прогноз: Forecast):Boolean
ForecastServiceController <<Facade>>->(создает)Forecast
iSensorRepo->(читает)ForecastServiceController <<Facade>>
iForecastRepo->(использует)ForecastServiceController <<Facade>>
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from domain.models import Прогноз, ДанныеСенсора
from domain.repositories import IForecastRepo, ISensorRepo

class ForecastServiceController:
    """
    Фасад сервиса прогнозирования
    C ForecastServiceController <<Facade>>
    """

    def __init__(self, forecast_repo: IForecastRepo, data_repo: ISensorRepo):
        """
        Конструктор получает репозитории через DI
        -forecastRepo: iForecastRepo
        -dataRepo: iSensorRepo
        """
        self.forecast_repo = forecast_repo
        self.data_repo = data_repo
        self.logger = logging.getLogger(__name__)
        self.доступные_модели = ["WRF-ARW", "GFS", "ICON-EU", "ECMWF"]

    async def запуститьМодель(self, типМодели: str, регион: str) -> Прогноз:
        """+запуститьМодель(типМодели:String,регион:String):Forecast"""
        self.logger.info(f"Запуск модели {типМодели} для региона {регион}")

        if типМодели not in self.доступные_модели:
            raise ValueError(f"Модель {типМодели} не поддерживается")

        try:
            # Сбор данных для инициализации модели
            данные_для_модели = await self._собратьДанныеДляМодели(регион)

            # Запуск модели (имитация)
            прогноз = await self._запуститьРасчетМодели(типМодели, регион, данные_для_модели)

            # Сохранение результата
            self.forecast_repo.сохранить(прогноз)

            self.logger.info(f"Прогноз создан: {прогноз.идПрогноза}")

            return прогноз

        except Exception as e:
            self.logger.error(f"Ошибка запуска модели {типМодели}: {e}")
            raise

    async def верифицироватьПрогноз(self, прогноз: Прогноз) -> bool:
        """+верефицироватьПрогноз(прогноз: Forecast):Boolean"""
        self.logger.info(f"Верификация прогноза {прогноз.идПрогноза}")

        try:
            # Получение фактических данных за период прогноза
            фактические_данные = await self._получитьФактическиеДанные(прогноз)

            # Сравнение прогноза с фактическими данными
            точность = await self._рассчитатьТочность(прогноз, фактические_данные)

            # Запись результата верификации
            результат = точность >= 0.7  # Порог точности 70%

            self.logger.info(
                f"Верификация прогноза: точность {точность:.2%}, "
                f"результат: {'УСПЕХ' if результат else 'НЕУДАЧА'}"
            )

            return результат

        except Exception as e:
            self.logger.error(f"Ошибка верификации прогноза: {e}")
            return False

    async def _собратьДанныеДляМодели(self, регион: str) -> Dict[str, Any]:
        """Сбор данных для инициализации модели прогноза"""
        # Определение временного диапазона (последние 24 часа)
        конец = int(datetime.now().timestamp() * 1000)
        начало = конец - (24 * 3600 * 1000)

        # Получение данных через iSensorRepo
        данные = self.data_repo.получитьЗаПериод(начало, конец)

        # Группировка данных
        сгруппированные_данные = {}
        for запись in данные:
            if запись.типИзмерения not in сгруппированные_данные:
                сгруппированные_данные[запись.типИзмерения] = []
            сгруппированные_данные[запись.типИзмерения].append(запись.значение)

        # Расчет средних значений
        начальные_условия = {}
        for тип, значения in сгруппированные_данные.items():
            if значения:
                начальные_условия[тип] = sum(значения) / len(значения)

        return начальные_условия

    async def _запуститьРасчетМодели(self, модель: str, регион: str,
                                   данные: Dict[str, Any]) -> Прогноз:
        """Имитация расчета модели прогноза"""
        await asyncio.sleep(0.5)  # Имитация расчета

        сейчас = int(datetime.now().timestamp() * 1000)

        # Базовые значения из входных данных
        базовая_температура = данные.get("temperature", 15.0)
        базовая_влажность = данные.get("humidity", 60.0)

        # Корректировка в зависимости от модели
        корректировки = {
            "WRF-ARW": {"temp_factor": 1.0, "precip_factor": 1.2},
            "GFS": {"temp_factor": 0.95, "precip_factor": 0.8},
            "ICON-EU": {"temp_factor": 1.05, "precip_factor": 1.0},
            "ECMWF": {"temp_factor": 1.02, "precip_factor": 0.9}
        }

        корректировка = корректировки.get(модель, корректировки["WRF-ARW"])

        # Создание прогноза
        прогноз = Прогноз(
            идПрогноза=f"forecast_{модель}_{сейчас}",
            датаСоздания=сейчас,
            температура=базовая_температура * корректировка["temp_factor"],
            вероятностьОсадков=int(базовая_влажность * корректировка["precip_factor"] / 100 * 100),
            влажность=int(базовая_влажность),
            давление=данные.get("pressure", 750.0),
            скоростьВетра=данные.get("wind_speed", 5.0),
            регион=регион
        )

        return прогноз

    async def _получитьФактическиеДанные(self, прогноз: Прогноз) -> List[ДанныеСенсора]:
        """Получение фактических данных для верификации"""
        # Генерация тестовых фактических данных
        фактические = []
        шаг = 3600 * 1000  # 1 час

        время = прогноз.датаСоздания
        конец = прогноз.датаСоздания + (12 * 3600 * 1000)

        while время <= конец:
            # Добавляем случайность к прогнозу
            фактические.append(ДанныеСенсора(
                идДанных=f"fact_{время}_temp",
                времяИзмерения=время,
                значение=прогноз.температура + (hash(str(время)) % 10 - 5),
                типИзмерения="temperature"
            ))
            время += шаг

        return фактические

    async def _рассчитатьТочность(self, прогноз: Прогноз,
                                фактические_данные: List[ДанныеСенсора]) -> float:
        """Расчет точности прогноза"""
        if not фактические_данные:
            return 0.0

        # Для упрощения сравниваем только температуру
        фактические_температуры = [
            д.значение for д in фактические_данные
            if д.типИзмерения == "temperature"
        ]

        if not фактические_температуры:
            return 0.0

        средняя_фактическая = sum(фактические_температуры) / len(фактические_температуры)

        # Расчет ошибки
        ошибка = abs(прогноз.температура - средняя_фактическая)
        макс_ошибка = 10.0

        точность = max(0, 1 - (ошибка / макс_ошибка))
        return точность

    async def запуститьАнсамбльМоделей(self, регион: str,
                                     модели: List[str] = None) -> List[Прогноз]:
        """Запуск ансамбля моделей"""
        if модели is None:
            модели = self.доступные_модели[:3]

        self.logger.info(f"Запуск ансамбля из {len(модели)} моделей")

        задачи = []
        for модель in модели:
            задачи.append(self.запуститьМодель(модель, регион))

        прогнозы = await asyncio.gather(*задачи, return_exceptions=True)

        # Фильтрация успешных результатов
        успешные_прогнозы = []
        for i, прогноз in enumerate(прогнозы):
            if isinstance(прогноз, Exception):
                self.logger.error(f"Ошибка в модели {модели[i]}: {прогноз}")
            else:
                успешные_прогнозы.append(прогноз)

        return успешные_прогнозы