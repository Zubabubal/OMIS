"""
DataIngestionController <<Facade>> из диаграммы контроллеров
C DataIngestionController <<Facade>>
-dataRepo: iSensorRepo
+опроситьИсточники():void
+обработатьДанные(данные:List<SensorData>):void
DataIngestionController <<Facade>>->(создает)SensorData
"""

import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid

from domain.models import ДанныеСенсора
from domain.repositories import ISensorRepo


class DataIngestionController:
    """
    Фасад для приема данных с метеостанций
    C DataIngestionController <<Facade>>
    """

    def __init__(self, data_repo: ISensorRepo):
        """
        Конструктор получает iSensorRepo через DI
        -dataRepo: iSensorRepo
        """
        self.data_repo = data_repo
        self.logger = logging.getLogger(__name__)
        self.активные_источники = ["station_26850", "station_26851", "radar_minsk"]

    async def опроситьИсточники(self) -> List[ДанныеСенсора]:
        """+опроситьИсточники():void"""
        self.logger.info("Опрос источников данных...")

        все_данные: List[ДанныеСенсора] = []

        for источник in self.активные_источники:
            try:
                данные = await self._запроситьДанныеСИсточника(источник)
                все_данные.extend(данные)
                self.logger.info(f"Источник {источник}: получено {len(данные)} записей")
            except Exception as e:
                self.logger.error(f"Ошибка опроса источника {источник}: {e}")

        # Обработка полученных данных
        await self.обработатьДанные(все_данные)

        self.logger.info(f"Всего получено и обработано {len(все_данные)} записей")
        return все_данные

    async def обработатьДанные(self, данные: List[ДанныеСенсора]) -> None:
        """+обработатьДанные(данные:List<SensorData>):void"""
        self.logger.info(f"Обработка {len(данные)} записей данных")

        обработанные_данные = []

        for запись in данные:
            try:
                # Валидация данных
                if self._валидироватьДанные(запись):
                    # Нормализация значений
                    нормализованная = self._нормализоватьДанные(запись)
                    обработанные_данные.append(нормализованная)

                    # Сохранение в репозиторий
                    self.data_repo.сохранить(нормализованная)

                    # DataIngestionController <<Facade>>->(создает)SensorData
                    self.logger.debug(f"Созданы SensorData: {запись.идДанных}")
                else:
                    self.logger.warning(f"Невалидные данные: {запись.идДанных}")
            except Exception as e:
                self.logger.error(f"Ошибка обработки данных {запись.идДанных}: {e}")

        self.logger.info(f"Обработано {len(обработанные_данные)} записей")

    async def _запроситьДанныеСИсточника(self, источник: str) -> List[ДанныеСенсора]:
        """Имитация запроса данных с источника"""
        await asyncio.sleep(0.1)  # Имитация задержки сети

        сейчас = int(datetime.now().timestamp() * 1000)
        данные = []

        if "station" in источник:
            station_id = источник.split("_")[1]

            данные.extend([
                ДанныеСенсора(
                    идДанных=f"{station_id}_temp_{сейчас}",
                    времяИзмерения=сейчас,
                    значение=15.0 + (int(station_id) % 10),
                    типИзмерения="temperature"
                ),
                ДанныеСенсора(
                    идДанных=f"{station_id}_hum_{сейчас}",
                    времяИзмерения=сейчас,
                    значение=60.0 + (int(station_id) % 20),
                    типИзмерения="humidity"
                ),
                ДанныеСенсора(
                    идДанных=f"{station_id}_pres_{сейчас}",
                    времяИзмерения=сейчас,
                    значение=750.0 + (int(station_id) % 10),
                    типИзмерения="pressure"
                ),
                ДанныеСенсора(
                    идДанных=f"{station_id}_wind_{сейчас}",
                    времяИзмерения=сейчас,
                    значение=5.0 + (int(station_id) % 15),
                    типИзмерения="wind_speed"
                )
            ])

        elif "radar" in источник:
            данные.append(ДанныеСенсора(
                идДанных=f"radar_precip_{сейчас}",
                времяИзмерения=сейчас,
                значение=2.5,
                типИзмерения="precipitation"
            ))

        return данные

    def _валидироватьДанные(self, данные: ДанныеСенсора) -> bool:
        """Валидация данных сенсора"""
        диапазоны = {
            "temperature": (-60, 60),
            "humidity": (0, 100),
            "pressure": (600, 800),
            "wind_speed": (0, 100),
            "precipitation": (0, 500)
        }

        if данные.типИзмерения not in диапазоны:
            return False

        мин, макс = диапазоны[данные.типИзмерения]
        return мин <= данные.значение <= макс

    def _нормализоватьДанные(self, данные: ДанныеСенсора) -> ДанныеСенсора:
        """Нормализация данных"""
        точность = {
            "temperature": 1,
            "humidity": 1,
            "pressure": 0,
            "wind_speed": 1,
            "precipitation": 2
        }

        if данные.типИзмерения in точность:
            значение = round(данные.значение, точность[данные.типИзмерения])
        else:
            значение = round(данные.значение, 2)

        return ДанныеСенсора(
            идДанных=данные.идДанных,
            времяИзмерения=данные.времяИзмерения,
            значение=значение,
            типИзмерения=данные.типИзмерения
        )

    async def добавитьИсточник(self, источник: str) -> None:
        """Добавление нового источника данных"""
        if источник not in self.активные_источники:
            self.активные_источники.append(источник)
            self.logger.info(f"Добавлен новый источник: {источник}")

    async def получитьСтатусИсточников(self) -> Dict[str, Any]:
        """Получение статуса всех источников"""
        статусы = {}
        for источник in self.активные_источники:
            статусы[источник] = {
                "активен": True,
                "последний_опрос": datetime.now().isoformat(),
                "тип": "станция" if "station" in источник else "радар"
            }

        return {
            "всего_источников": len(self.активные_источники),
            "статусы": статусы
        }