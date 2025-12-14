"""
Controller_Factory из диаграммы
C Controller_Factory <<Abstract Factory>>
+создатьDataController(): DataController
+создатьForecastController(): ForecastController
Controller_Factory->(получает зависимости) DI_Container
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.di_container import DI_Container
    from controllers.data_ingestion_controller import DataIngestionController
    from controllers.forecast_service_controller import ForecastServiceController


class ControllerFactory(ABC):
    """
    Abstract Factory для создания контроллеров
    C Controller_Factory <<Abstract Factory>>
    """

    @abstractmethod
    def создатьDataController(self) -> 'DataIngestionController':
        """+создатьDataController(): DataController"""
        pass

    @abstractmethod
    def создатьForecastController(self) -> 'ForecastServiceController':
        """+создатьForecastController(): ForecastController"""
        pass


class WeatherControllerFactory(ControllerFactory):
    """Конкретная фабрика контроллеров погодной системы"""

    def __init__(self, di_container: 'DI_Container' = None):
        """
        Конструктор получает DI контейнер
        Controller_Factory->(получает зависимости) DI_Container
        """
        self.di_container = di_container

    def создатьDataController(self) -> 'DataIngestionController':
        """Создание DataIngestionController"""
        try:
            from controllers.data_ingestion_controller import DataIngestionController
            from domain.repositories import SensorDataRepository

            if self.di_container:
                # Получаем зависимости через DI
                data_repo = self.di_container.разрешить(SensorDataRepository)
                return DataIngestionController(data_repo)
            else:
                # Создаем зависимости напрямую
                data_repo = SensorDataRepository()
                return DataIngestionController(data_repo)
        except ImportError as e:
            # Возвращаем заглушку, если контроллер не реализован
            print(f"⚠️ DataIngestionController не найден: {e}")
            return None

    def создатьForecastController(self) -> 'ForecastServiceController':
        """Создание ForecastServiceController"""
        try:
            from controllers.forecast_service_controller import ForecastServiceController
            from domain.repositories import ForecastRepository, SensorDataRepository

            if self.di_container:
                # Получаем зависимости через DI
                forecast_repo = self.di_container.разрешить(ForecastRepository)
                data_repo = self.di_container.разрешить(SensorDataRepository)
                return ForecastServiceController(forecast_repo, data_repo)
            else:
                # Создаем зависимости напрямую
                forecast_repo = ForecastRepository()
                data_repo = SensorDataRepository()
                return ForecastServiceController(forecast_repo, data_repo)
        except ImportError as e:
            # Возвращаем заглушку, если контроллер не реализован
            print(f"⚠️ ForecastServiceController не найден: {e}")
            return None


class SimpleControllerFactory(ControllerFactory):
    """Простая фабрика для тестов"""

    def создатьDataController(self):
        print("⚠️ DataController создается через SimpleControllerFactory")
        return None

    def создатьForecastController(self):
        print("⚠️ ForecastController создается через SimpleControllerFactory")
        return None