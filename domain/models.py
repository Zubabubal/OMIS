"""
Модели данных системы согласно диаграмме
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, TypeVar, Generic
import statistics

T = TypeVar('T')


class AlertLevel(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    DANGER = "danger"


@dataclass
class GeoPoint:
    """Географическая точка"""
    latitude: float
    longitude: float

    def __str__(self) -> str:
        return f"{self.latitude:.4f},{self.longitude:.4f}"


@dataclass
class ДанныеСенсора:
    """
    C ДанныеСенсора
    -идДанных:String
    -времяИзмерения:Long
    -значение:Double
    -типИзмерения:String
    """
    идДанных: str
    времяИзмерения: int  # timestamp в миллисекундах
    значение: float
    типИзмерения: str

    def to_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.времяИзмерения / 1000)

    @classmethod
    def from_weather_data(cls, weather_data: 'WeatherData') -> List['ДанныеСенсора']:
        timestamp = int(weather_data.timestamp.timestamp() * 1000)

        return [
            ДанныеСенсора(
                идДанных=f"{weather_data.id}_temp",
                времяИзмерения=timestamp,
                значение=weather_data.temperature,
                типИзмерения="temperature"
            ),
            ДанныеСенсора(
                идДанных=f"{weather_data.id}_hum",
                времяИзмерения=timestamp,
                значение=weather_data.humidity,
                типИзмерения="humidity"
            ),
            ДанныеСенсора(
                идДанных=f"{weather_data.id}_pres",
                времяИзмерения=timestamp,
                значение=weather_data.pressure,
                типИзмерения="pressure"
            ),
            ДанныеСенсора(
                идДанных=f"{weather_data.id}_wind",
                времяИзмерения=timestamp,
                значение=weather_data.wind_speed,
                типИзмерения="wind_speed"
            )
        ]


@dataclass
class Метеостанция:
    """
    C Метеостанция
    -идСтанции:String
    -координаты:GeoPoint
    -статус:String
    +активировать():void
    """
    идСтанции: str
    координаты: GeoPoint
    статус: str = "неактивна"

    def активировать(self) -> None:
        self.статус = "активна"

    def деактивировать(self) -> None:
        self.статус = "неактивна"


@dataclass
class Оповещение:
    """
    C Оповещение
    -идОповещения:String
    -типОпасности:String
    -текстСообщения:String
    +проверитьАктуальность(текущееВремя:Long):Boolean
    """
    идОповещения: str
    типОпасности: str
    текстСообщения: str
    времяСоздания: int
    времяИстечения: int
    уровень: str = "warning"

    def проверитьАктуальность(self, текущееВремя: int) -> bool:
        return self.времяСоздания <= текущееВремя <= self.времяИстечения

    def to_alert(self) -> 'Alert':
        level_mapping = {
            "info": AlertLevel.OK,
            "warning": AlertLevel.WARNING,
            "danger": AlertLevel.DANGER
        }

        return Alert(
            id=self.идОповещения,
            level=level_mapping.get(self.уровень, AlertLevel.WARNING),
            type=self.типОпасности,
            region="Общий",
            valid_from=datetime.fromtimestamp(self.времяСоздания / 1000),
            valid_to=datetime.fromtimestamp(self.времяИстечения / 1000),
            description=self.текстСообщения,
            is_active=True
        )


@dataclass
class Прогноз:
    """
    C Прогноз
    -идПрогноза:String
    -датаСоздания:Long
    -температура:Double
    -вероятностьОсадков: Integer
    """
    идПрогноза: str
    датаСоздания: int
    температура: float
    вероятностьОсадков: int
    влажность: Optional[int] = None
    давление: Optional[float] = None
    скоростьВетра: Optional[float] = None
    регион: str = "Минск"

    def to_forecast(self) -> 'Forecast':
        creation_time = datetime.fromtimestamp(self.датаСоздания / 1000)

        points = []
        for i in range(0, 73, 3):
            forecast_time = creation_time + timedelta(hours=i)
            points.append({
                "time": forecast_time.strftime("%H:%M"),
                "temperature": self.температура + (i * 0.1 - 3.6),
                "humidity": self.влажность if self.влажность else 60,
                "wind_speed": self.скоростьВетра if self.скоростьВетра else 5.0
            })

        return Forecast(
            id=self.идПрогноза,
            model_type="Базовая модель",
            calculation_time=creation_time,
            valid_from=creation_time,
            valid_to=creation_time + timedelta(hours=72),
            region=self.регион,
            points=points
        )


@dataclass
class WeatherData:
    """Данные с метеостанции"""
    id: str
    station_id: str
    timestamp: datetime
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: str
    precipitation: float
    phenomena: str = ""

    def to_данные_сенсора(self) -> List[ДанныеСенсора]:
        return ДанныеСенсора.from_weather_data(self)


@dataclass
class Forecast:
    """Прогноз погоды"""
    id: str
    model_type: str
    calculation_time: datetime
    valid_from: datetime
    valid_to: datetime
    region: str
    points: List[Dict[str, Any]] = field(default_factory=list)

    def to_прогноз(self) -> Прогноз:
        if not self.points:
            avg_temp = 0.0
            avg_humidity = 0
        else:
            temps = [p.get("temperature", 0) for p in self.points]
            avg_temp = statistics.mean(temps) if temps else 0.0
            humidity = [p.get("humidity", 0) for p in self.points]
            avg_humidity = int(statistics.mean(humidity)) if humidity else 0

        return Прогноз(
            идПрогноза=self.id,
            датаСоздания=int(self.calculation_time.timestamp() * 1000),
            температура=avg_temp,
            вероятностьОсадков=min(100, avg_humidity),
            влажность=avg_humidity,
            регион=self.region
        )


@dataclass
class Alert:
    """Штормовое предупреждение"""
    id: str
    level: AlertLevel
    type: str
    region: str
    valid_from: datetime
    valid_to: datetime
    description: str
    is_active: bool = True

    def to_оповещение(self) -> Оповещение:
        level_mapping = {
            AlertLevel.OK: "info",
            AlertLevel.WARNING: "warning",
            AlertLevel.CRITICAL: "warning",
            AlertLevel.DANGER: "danger"
        }

        return Оповещение(
            идОповещения=self.id,
            типОпасности=self.type,
            текстСообщения=self.description,
            времяСоздания=int(self.valid_from.timestamp() * 1000),
            времяИстечения=int(self.valid_to.timestamp() * 1000),
            уровень=level_mapping.get(self.level, "warning")
        )


@dataclass
class ModelParameters:
    """Параметры модели прогноза"""
    algorithm: str = "WRF-ARW (Mesoscale)"
    initial_conditions: str = "Текущие (Real-time)"
    grid_resolution: str = "3 км (Высокое)"
    forecast_horizon: int = 72