"""
Application_Bootstrap из диаграммы
C Application_Bootstrap <<main>>
+main(args:String[]):void
+инициализироватьСистему(конфиг:Config):void
Application_Bootstrap->(использует)Configuration_Manager
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Type

from .config_manager import ConfigurationManager
from .di_container import DI_Container
from .controller_factory import ControllerFactory, WeatherControllerFactory


class Application_Bootstrap:
    """Точка входа и инициализации системы"""

    _instance = None
    _di_container = None
    _config = None
    _running = False

    @staticmethod
    def main(args: list = None) -> None:
        """+main(args:String[]):void"""
        if args is None:
            args = []

        print("=" * 60)
        print("Запуск системы мониторинга погоды")
        print("=" * 60)

        # Настройка обработки сигналов
        signal.signal(signal.SIGINT, Application_Bootstrap._handle_shutdown)
        signal.signal(signal.SIGTERM, Application_Bootstrap._handle_shutdown)

        # Загрузка конфигурации
        config_manager = ConfigurationManager()
        config = config_manager.загрузитьНастройки()

        # Инициализация системы
        Application_Bootstrap.инициализироватьСистему(config)

        # Запуск асинхронной работы
        try:
            asyncio.run(Application_Bootstrap._run_system())
        except KeyboardInterrupt:
            print("\nСистема остановлена пользователем")
        except Exception as e:
            print(f"\nКритическая ошибка: {e}")
            sys.exit(1)

    @staticmethod
    def инициализироватьСистему(config: Dict[str, Any]) -> None:
        """+инициализироватьСистему(конфиг:Config):void"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('weather_system.log'),
                logging.StreamHandler()
            ]
        )

        logger = logging.getLogger(__name__)
        logger.info("Инициализация системы...")

        # Создание DI контейнера
        di_container = DI_Container()

        # Регистрация компонентов в DI контейнере
        Application_Bootstrap._register_components(di_container, config)

        # Сохранение глобальных объектов
        Application_Bootstrap._di_container = di_container
        Application_Bootstrap._config = config

        logger.info("Система инициализирована успешно")

    @staticmethod
    def _register_components(di_container: 'DI_Container', config: Dict[str, Any]) -> None:
        """Регистрация всех компонентов в DI контейнере"""
        from domain.repositories import (
            WeatherDataRepository,
            ForecastRepository,
            AlertRepository,
            SensorDataRepository
        )
        from services.forecast_service import ForecastService
        from services.alert_service import AlertService
        from controllers.data_controller import DataController
        from controllers.forecast_controller import ForecastController
        from controllers.alerts_controller import AlertsAlertController
        from controllers.data_ingestion_controller import DataIngestionController
        from controllers.forecast_service_controller import ForecastServiceController
        from controllers.report_controller import ReportController
        from controllers.analysis_alert_controller import AnalysisAlertController

        # Добавляем импорт панелей
        try:
            from views.meteorologist_panel import ПанельМетеоролога
            from views.climatologist_panel import ПанельКлиматолога
        except ImportError:
            # Если панели еще не созданы, пропускаем
            ПанельМетеоролога = None
            ПанельКлиматолога = None

        # Регистрация репозиториев
        di_container.зарегистрировать(WeatherDataRepository, WeatherDataRepository)
        di_container.зарегистрировать(ForecastRepository, ForecastRepository)
        di_container.зарегистрировать(AlertRepository, AlertRepository)
        di_container.зарегистрировать(SensorDataRepository, SensorDataRepository)

        # Регистрация сервисов
        di_container.зарегистрировать(ForecastService, ForecastService)
        di_container.зарегистрировать(AlertService, AlertService)

        # Регистрация контроллеров
        di_container.зарегистрировать(DataController, DataController)
        di_container.зарегистрировать(ForecastController, ForecastController)
        di_container.зарегистрировать(AlertsAlertController, AlertsAlertController)
        di_container.зарегистрировать(DataIngestionController, DataIngestionController)
        di_container.зарегистрировать(ForecastServiceController, ForecastServiceController)
        di_container.зарегистрировать(ReportController, ReportController)
        di_container.зарегистрировать(AnalysisAlertController, AnalysisAlertController)

        # Регистрация панелей (если они существуют)
        if ПанельМетеоролога:
            di_container.зарегистрировать(ПанельМетеоролога, ПанельМетеоролога)
        if ПанельКлиматолога:
            di_container.зарегистрировать(ПанельКлиматолога, ПанельКлиматолога)

        # Регистрация фабрики
        di_container.зарегистрировать(ControllerFactory, WeatherControllerFactory)

        # Сохранение конфигурации - создаем специальный класс-обертку
        class ConfigWrapper:
            def __init__(self, config_dict: Dict[str, Any]):
                self._config = config_dict

            def get(self, key: str, default=None):
                keys = key.split('.')
                value = self._config
                for k in keys:
                    if isinstance(value, dict):
                        value = value.get(k, {})
                    else:
                        return default
                return value if value != {} else default

            def __getitem__(self, key):
                return self._config[key]

            def __contains__(self, key):
                return key in self._config

        # Регистрируем обертку вместо сырого Dict
        config_wrapper = ConfigWrapper(config)
        di_container.зарегистрировать(ConfigWrapper, config_wrapper, is_instance=True)

        # Также регистрируем как словарь для обратной совместимости
        #di_container.зарегистрировать(dict, config, is_instance=True)

    @staticmethod
    async def _run_system() -> None:
        """Запуск основной работы системы"""
        logger = logging.getLogger(__name__)
        logger.info("Запуск системных задач...")

        Application_Bootstrap._running = True

        try:
            # Получение фабрики контроллеров
            factory = Application_Bootstrap._di_container.разрешить(ControllerFactory)

            # Создание контроллеров через фабрику
            data_ingestion_controller = factory.создатьDataController()
            forecast_service_controller = factory.создатьForecastController()

            if data_ingestion_controller:
                logger.info(f"Создан DataIngestionController: {type(data_ingestion_controller).__name__}")
            else:
                logger.warning("DataIngestionController не создан")

            if forecast_service_controller:
                logger.info(f"Создан ForecastServiceController: {type(forecast_service_controller).__name__}")
            else:
                logger.warning("ForecastServiceController не создан")

        except Exception as e:
            logger.error(f"Ошибка создания контроллеров: {e}")
            logger.info("Продолжаем без контроллеров...")

        # Запуск веб-сервера (если есть)
        try:
            from web.api_server import WeatherAPIServer
            api_server = WeatherAPIServer(Application_Bootstrap._di_container)
            await api_server.start()
            logger.info("Веб-сервер запущен")
        except ImportError as e:
            logger.info(f"Веб-сервер не запущен (модуль не найден): {e}")
        except Exception as e:
            logger.warning(f"Веб-сервер не запущен: {e}")

        # Демонстрация работы системы
        await Application_Bootstrap._demonstrate_system()

        # Держим систему запущенной
        while Application_Bootstrap._running:
            await asyncio.sleep(1)

        logger.info("Система завершила работу")

    @staticmethod
    async def _demonstrate_system() -> None:
        """Демонстрация работы системы"""
        logger = logging.getLogger(__name__)
        logger.info("Демонстрация работы системы...")

        # Получаем DI контейнер
        di_container = Application_Bootstrap._di_container

        # Пример: создаем прогноз
        try:
            from domain.models import ModelParameters
            from controllers.forecast_controller import ForecastController

            forecast_controller = di_container.разрешить(ForecastController)

            # Тестовые параметры
            params = ModelParameters(
                algorithm="WRF-ARW",
                initial_conditions="Текущие",
                grid_resolution="3 км",
                forecast_horizon=72
            )

            # Расчет прогноза
            forecast = await forecast_controller.calculate_forecast("Минск", params)
            logger.info(f"Прогноз создан: {forecast.id}")

            # Получение последнего прогноза
            latest = await forecast_controller.get_latest_forecast("Минск")
            if latest:
                logger.info(f"Последний прогноз: {latest.id}")

        except Exception as e:
            logger.error(f"Ошибка демонстрации: {e}")

    @staticmethod
    def _handle_shutdown(signum, frame):
        """Обработка сигнала завершения"""
        print("\nПолучен сигнал завершения...")
        Application_Bootstrap._running = False

    @staticmethod
    def get_di_container() -> 'DI_Container':
        """Получение DI контейнера"""
        return Application_Bootstrap._di_container

    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Получение конфигурации"""
        return Application_Bootstrap._config