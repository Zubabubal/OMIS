"""
Репозитории системы согласно диаграмме
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic, Dict, Any
from datetime import datetime, timedelta
import uuid

T = TypeVar('T')


class IRepository(Generic[T], ABC):
    """
    I iRepository<T>
    +найтиПоИд(ид:String):T
    +сохранить(entity:T):void
    +найтиВсе():List<T>
    """

    @abstractmethod
    def найтиПоИд(self, ид: str) -> Optional[T]:
        pass

    @abstractmethod
    def сохранить(self, entity: T) -> None:
        pass

    @abstractmethod
    def найтиВсе(self) -> List[T]:
        pass


class IAlertRepo(ABC):
    """I iAiertRepo"""

    @abstractmethod
    def найтиАктуальные(self, текущееВремя: int) -> List['Оповещение']:
        pass


class IForecastRepo(ABC):
    """I iForecastRepo"""

    @abstractmethod
    def получитьАктуальные(self, регион: str) -> List['Прогноз']:
        """+получитьАктуальные(регион:String):List<Forecast>"""
        pass


class ISensorRepo(ABC):
    """I iSensorRepo"""

    @abstractmethod
    def получитьЗаПериод(self, начало: int, конец: int) -> List['ДанныеСенсора']:
        """+получитьЗаПериод(начало:Long,конец:Long):List<SensorData>"""
        pass


class AlertRepository(IRepository['Alert'], IAlertRepo):
    """
    C AiertRepository
    AiertRepository->iRepository<Aiert>
    AiertRepository->iAiertRepo
    """

    def __init__(self):
        self._storage: Dict[str, 'Alert'] = {}
        self._оповещения: Dict[str, 'Оповещение'] = {}

    def найтиПоИд(self, ид: str) -> Optional['Alert']:
        return self._storage.get(ид)

    def сохранить(self, entity: 'Alert') -> None:
        self._storage[entity.id] = entity
        оповещение = entity.to_оповещение()
        self._оповещения[оповещение.идОповещения] = оповещение

    def найтиВсе(self) -> List['Alert']:
        return list(self._storage.values())

    def найтиАктуальные(self, текущееВремя: int) -> List['Оповещение']:
        актуальные = []
        for оповещение in self._оповещения.values():
            if оповещение.проверитьАктуальность(текущееВремя):
                актуальные.append(оповещение)
        return актуальные

    async def get_active_alerts(self) -> List['Alert']:
        now = datetime.now()
        return [
            alert for alert in self._storage.values()
            if alert.is_active and alert.valid_from <= now <= alert.valid_to
        ]

    async def save(self, alert: 'Alert') -> None:
        self.сохранить(alert)

    async def get_by_id(self, alert_id: str) -> Optional['Alert']:
        return self.найтиПоИд(alert_id)

    async def get_all(self) -> List['Alert']:
        return self.найтиВсе()


class ForecastRepository(IRepository['Forecast'], IForecastRepo):
    """
    C ForecastRepository
    +получитьАктуальные(регион:String):List<Forecast>
    ForecastRepository->iRepository<forecast>
    ForecastRepository->iForecastRepo
    """

    def __init__(self):
        self._storage: Dict[str, 'Forecast'] = {}
        self._прогнозы: Dict[str, 'Прогноз'] = {}
        self._region_index: Dict[str, List[str]] = {}

    def найтиПоИд(self, ид: str) -> Optional['Forecast']:
        return self._storage.get(ид)

    def сохранить(self, entity: 'Forecast') -> None:
        self._storage[entity.id] = entity
        прогноз = entity.to_прогноз()
        self._прогнозы[прогноз.идПрогноза] = прогноз

        if entity.region not in self._region_index:
            self._region_index[entity.region] = []
        if entity.id not in self._region_index[entity.region]:
            self._region_index[entity.region].append(entity.id)

    def найтиВсе(self) -> List['Forecast']:
        return list(self._storage.values())

    def получитьАктуальные(self, регион: str) -> List['Прогноз']:
        if регион not in self._region_index:
            return []

        актуальные = []
        текущееВремя = int(datetime.now().timestamp() * 1000)

        for прогноз_id in self._region_index[регион]:
            прогноз = self._прогнозы.get(прогноз_id)
            if прогноз:
                if текущееВремя - прогноз.датаСоздания <= 24 * 3600 * 1000:
                    актуальные.append(прогноз)

        return актуальные

    async def get_all_for_region(self, region: str) -> List['Forecast']:
        if region not in self._region_index:
            return []

        forecasts = []
        for forecast_id in self._region_index[region]:
            forecast = self._storage.get(forecast_id)
            if forecast:
                forecasts.append(forecast)

        return forecasts

    async def get_latest_for_region(self, region: str) -> Optional['Forecast']:
        forecasts = await self.get_all_for_region(region)
        if not forecasts:
            return None
        return max(forecasts, key=lambda x: x.calculation_time)

    async def save(self, forecast: 'Forecast') -> None:
        self.сохранить(forecast)

    async def get_by_id(self, forecast_id: str) -> Optional['Forecast']:
        return self.найтиПоИд(forecast_id)

    async def get_all(self) -> List['Forecast']:
        return self.найтиВсе()


class SensorDataRepository(IRepository['ДанныеСенсора'], ISensorRepo):
    """
    C SensorDataRepostory
    +получитьЗаПериод(начало:Long,конец:Long):List<SensorData>
    SensorDataRepostory->iRepository<SensorData>
    SensorDataRepostory->iSensorRepo
    """

    def __init__(self):
        self._storage: Dict[str, 'ДанныеСенсора'] = {}
        self._time_index: Dict[int, List[str]] = {}

    def найтиПоИд(self, ид: str) -> Optional['ДанныеСенсора']:
        return self._storage.get(ид)

    def сохранить(self, entity: 'ДанныеСенсора') -> None:
        self._storage[entity.идДанных] = entity

        if entity.времяИзмерения not in self._time_index:
            self._time_index[entity.времяИзмерения] = []
        if entity.идДанных not in self._time_index[entity.времяИзмерения]:
            self._time_index[entity.времяИзмерения].append(entity.идДанных)

    def найтиВсе(self) -> List['ДанныеСенсора']:
        return list(self._storage.values())

    def получитьЗаПериод(self, начало: int, конец: int) -> List['ДанныеСенсора']:
        result = []
        for timestamp, ids in self._time_index.items():
            if начало <= timestamp <= конец:
                for data_id in ids:
                    data = self._storage.get(data_id)
                    if data:
                        result.append(data)

        result.sort(key=lambda x: x.времяИзмерения)
        return result

    def получитьПоТипу(self, тип: str) -> List['ДанныеСенсора']:
        return [data for data in self._storage.values()
                if data.типИзмерения == тип]


class WeatherDataRepository:
    """Репозиторий для WeatherData"""

    def __init__(self):
        self._data: Dict[str, 'WeatherData'] = {}
        self._station_data: Dict[str, List['WeatherData']] = {}

    async def save(self, weather_data: 'WeatherData') -> None:
        self._data[weather_data.id] = weather_data

        if weather_data.station_id not in self._station_data:
            self._station_data[weather_data.station_id] = []
        self._station_data[weather_data.station_id].append(weather_data)

    async def get_by_id(self, data_id: str) -> Optional['WeatherData']:
        return self._data.get(data_id)

    async def get_all(self) -> List['WeatherData']:
        return list(self._data.values())

    async def get_latest_by_station(self, station_id: str) -> Optional['WeatherData']:
        if station_id not in self._station_data or not self._station_data[station_id]:
            return None
        return max(self._station_data[station_id], key=lambda x: x.timestamp)

    async def get_station_history(self, station_id: str, hours: int = 24) -> List['WeatherData']:
        if station_id not in self._station_data:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [d for d in self._station_data[station_id]
                if d.timestamp >= cutoff_time]