"""
Интерфейсы представления согласно диаграмме
I ОсновнойИнтерфейс
I ПрогнозView
I АнализView
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ОсновнойИнтерфейс(ABC):
    """
    I ОсновнойИнтерфейс
    +отобразитьОшибку(текст:String):void
    """

    @abstractmethod
    def отобразитьОшибку(self, текст: str) -> None:
        """+отобразитьОшибку(текст:String):void"""
        pass

    @abstractmethod
    def отобразитьСообщение(self, текст: str, тип: str = "info") -> None:
        """Отображение сообщения"""
        pass

    @abstractmethod
    def обновитьСтатус(self, статус: str) -> None:
        """Обновление статуса системы"""
        pass


class ПрогнозView(ABC):
    """
    I ПрогнозView
    +показатьКартуПогоды(прогноз: Object):void
    +запроситьНовыйПрогноз():void
    """

    @abstractmethod
    def показатьКартуПогоды(self, прогноз: Dict[str, Any]) -> None:
        """+показатьКартуПогоды(прогноз: Object):void"""
        pass

    @abstractmethod
    def запроситьНовыйПрогноз(self) -> None:
        """+запроситьНовыйПрогноз():void"""
        pass

    @abstractmethod
    def обновитьПрогноз(self, данные: Dict[str, Any]) -> None:
        """Обновление данных прогноза"""
        pass

    @abstractmethod
    def показатьГрафикПрогноза(self, данные: List[Dict[str, Any]]) -> None:
        """Отображение графика прогноза"""
        pass


class АнализView(ABC):
    """
    I АнализView
    +построитьГрафикТрендов(данные:List):void
    +отобразитьТаблицуАномалий():void
    """

    @abstractmethod
    def построитьГрафикТрендов(self, данные: List[Dict[str, Any]]) -> None:
        """+построитьГрафикТрендов(данные:List):void"""
        pass

    @abstractmethod
    def отобразитьТаблицуАномалий(self) -> None:
        """+отобразитьТаблицуАномалий():void"""
        pass

    @abstractmethod
    def показатьКлиматическиеДанные(self, данные: Dict[str, Any]) -> None:
        """Отображение климатических данных"""
        pass

    @abstractmethod
    def обновитьСтатистику(self, статистика: Dict[str, Any]) -> None:
        """Обновление статистики"""
        pass


# Дополнительные интерфейсы из предыдущих диаграмм

class IMonitoringView(ABC):
    """Интерфейс представления мониторинга"""

    @abstractmethod
    def update_weather_data(self, weather_data: 'WeatherData') -> None:
        pass

    @abstractmethod
    def update_radar_data(self, radar_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def show_alert(self, message: str, level: 'AlertLevel') -> None:
        pass


class IModelingView(ABC):
    """Интерфейс представления моделирования"""

    @abstractmethod
    def set_model_parameters(self, parameters: 'ModelParameters') -> None:
        pass

    @abstractmethod
    def update_forecast_visualization(self, forecast: 'Forecast') -> None:
        pass

    @abstractmethod
    def show_simulation_progress(self, progress: int) -> None:
        pass


class IArchiveView(ABC):
    """Интерфейс представления архива"""

    @abstractmethod
    def display_climate_data(self, records: List['WeatherData']) -> None:
        pass

    @abstractmethod
    def display_statistics(self, statistics: Dict[str, Any]) -> None:
        pass


class IAlertsView(ABC):
    """Интерфейс представления оповещений"""

    @abstractmethod
    def display_alerts(self, alerts: List['Alert']) -> None:
        pass

    @abstractmethod
    def show_new_alert(self, alert: 'Alert') -> None:
        pass