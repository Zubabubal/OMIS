"""
DataController из диаграммы контроллеров
C DataEngineControler (вероятно DataController)
+stopSensor(sensorId: String): void
+getSensorData(sensorId: String): List<SensorData>! void
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from domain.models import WeatherData, ДанныеСенсора
from domain.repositories import WeatherDataRepository, SensorDataRepository


class DataController:
    """Контроллер управления данными"""

    def __init__(self, data_repository: WeatherDataRepository,
                 sensor_repository: SensorDataRepository):
        self.data_repository = data_repository
        self.sensor_repository = sensor_repository
        self.logger = logging.getLogger(__name__)
        self.active_stations: Dict[str, bool] = {
            "26850": True,
            "26851": True,
            "radar_minsk": True
        }

    async def ingest_data(self, weather_data: WeatherData) -> None:
        """Прием и сохранение данных"""
        await self.data_repository.save(weather_data)

        # Также сохраняем как SensorData
        sensor_data_list = weather_data.to_данные_сенсора()
        for sensor_data in sensor_data_list:
            self.sensor_repository.сохранить(sensor_data)

        self.logger.info(f"Данные сохранены: {weather_data.station_id}")

    async def stop_sensor(self, sensor_id: str) -> None:
        """+stopSensor(sensorId: String): void"""
        if sensor_id in self.active_stations:
            self.active_stations[sensor_id] = False
            self.logger.info(f"Сенсор {sensor_id} остановлен")
        else:
            self.logger.warning(f"Сенсор {sensor_id} не найден")

    async def get_sensor_data(self, sensor_id: str, hours: int = 24) -> List[ДанныеСенсора]:
        """+getSensorData(sensorId: String): List<SensorData>! void"""
        # Получение данных как WeatherData
        weather_data_list = await self.data_repository.get_station_history(sensor_id, hours)

        # Преобразование в SensorData
        sensor_data_list = []
        for weather_data in weather_data_list:
            sensor_data_list.extend(weather_data.to_данные_сенсора())

        self.logger.info(f"Получено {len(sensor_data_list)} записей для сенсора {sensor_id}")
        return sensor_data_list

    async def start_sensor(self, sensor_id: str) -> None:
        """Запуск сенсора"""
        self.active_stations[sensor_id] = True
        self.logger.info(f"Сенсор {sensor_id} запущен")

    async def get_sensor_status(self, sensor_id: str) -> Dict[str, Any]:
        """Получение статуса сенсора"""
        is_active = self.active_stations.get(sensor_id, False)
        latest_data = await self.data_repository.get_latest_by_station(sensor_id)

        return {
            "sensor_id": sensor_id,
            "is_active": is_active,
            "last_update": latest_data.timestamp.isoformat() if latest_data else None,
            "data_available": latest_data is not None
        }

    async def get_all_sensors_status(self) -> Dict[str, Dict[str, Any]]:
        """Статус всех сенсоров"""
        status_dict = {}
        for sensor_id in self.active_stations.keys():
            status_dict[sensor_id] = await self.get_sensor_status(sensor_id)
        return status_dict

    async def cleanup_old_data(self, days: int = 30) -> int:
        """Очистка старых данных"""
        cutoff_time = datetime.now() - timedelta(days=days)
        # В реальной системе здесь была бы очистка БД
        self.logger.info(f"Очистка данных старше {days} дней")
        return 0  # Возвращает количество удаленных записей