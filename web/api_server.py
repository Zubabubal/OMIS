"""
Веб-сервер API для системы
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.di_container import DI_Container
from domain.models import WeatherData, ModelParameters
from web.api_adapter import WebInterfaceAdapter


class WeatherAPIServer:
    """Веб-сервер системы мониторинга погоды"""

    def __init__(self, di_container: DI_Container):
        self.di_container = di_container
        self.app = FastAPI(
            title="Weather Monitoring System API",
            description="API для системы мониторинга и прогнозирования погоды",
            version="1.0.0"
        )

        self.logger = logging.getLogger(__name__)
        self.active_connections: Dict[str, WebSocket] = {}

        self._setup_middleware()
        self._setup_routes()
        self._setup_websockets()

    def _setup_middleware(self):
        """Настройка middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Настройка маршрутов API"""

        @self.app.get("/")
        async def root():
            """Корневой эндпоинт"""
            return {"message": "Weather Monitoring System API", "status": "running"}

        @self.app.get("/api/health")
        async def health_check():
            """Проверка здоровья системы"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }

        @self.app.get("/api/current-weather")
        async def get_current_weather(station_id: str = "26850"):
            """Получение текущей погоды"""
            try:
                from domain.repositories import WeatherDataRepository
                repo = self.di_container.разрешить(WeatherDataRepository)
                latest_data = await repo.get_latest_by_station(station_id)

                if latest_data:
                    return WebInterfaceAdapter.prepare_weather_data(latest_data)
                else:
                    return {"error": "Данные не найдены"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/forecast")
        async def get_forecast(region: str = "Минск"):
            """Получение прогноза"""
            try:
                from domain.repositories import ForecastRepository
                repo = self.di_container.разрешить(ForecastRepository)
                forecast = await repo.get_latest_for_region(region)

                if forecast:
                    return {
                        "forecast": WebInterfaceAdapter.prepare_forecast_chart_data(forecast),
                        "details": {
                            "id": forecast.id,
                            "model": forecast.model_type,
                            "region": forecast.region,
                            "calculation_time": forecast.calculation_time.isoformat()
                        }
                    }
                else:
                    return {"error": "Прогноз не найден"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/alerts")
        async def get_alerts(active_only: bool = True):
            """Получение оповещений"""
            try:
                from domain.repositories import AlertRepository
                repo = self.di_container.разрешить(AlertRepository)

                if active_only:
                    alerts = await repo.get_active_alerts()
                else:
                    alerts = await repo.get_all()

                return WebInterfaceAdapter.prepare_alerts_data(alerts)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/archive")
        async def get_archive(station_id: str = "26850", hours: int = 24):
            """Получение архивных данных"""
            try:
                from domain.repositories import WeatherDataRepository
                repo = self.di_container.разрешить(WeatherDataRepository)
                data = await repo.get_station_history(station_id, hours)

                return WebInterfaceAdapter.prepare_archive_data(data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/modeling/parameters")
        async def get_modeling_parameters():
            """Получение параметров моделирования"""
            return WebInterfaceAdapter.prepare_modeling_parameters()

        @self.app.get("/api/alerts/types")
        async def get_alert_types():
            """Получение типов оповещений"""
            return WebInterfaceAdapter.prepare_alert_types()

        @self.app.get("/api/regions")
        async def get_regions():
            """Получение списка регионов"""
            return WebInterfaceAdapter.prepare_regions()

        @self.app.post("/api/modeling/calculate")
        async def calculate_forecast(params: Dict[str, Any]):
            """Расчет прогноза"""
            try:
                from controllers.forecast_service_controller import ForecastServiceController
                controller = self.di_container.разрешить(ForecastServiceController)

                model_params = ModelParameters(
                    algorithm=params.get("algorithm", "WRF-ARW (Mesoscale)"),
                    initial_conditions=params.get("initial_conditions", "Текущие (Real-time)"),
                    grid_resolution=params.get("grid_resolution", "3 км (Высокое)"),
                    forecast_horizon=int(params.get("forecast_horizon", 72))
                )

                region = params.get("region", "Минск")
                forecast = await controller.запуститьМодель(model_params.algorithm, region)

                return {
                    "status": "success",
                    "forecast_id": forecast.идПрогноза,
                    "message": f"Прогноз для {region} создан успешно"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/alerts/create")
        async def create_alert(alert_data: Dict[str, Any]):
            """Создание оповещения"""
            try:
                from controllers.alerts_controller import AlertsAlertController
                controller = self.di_container.разрешить(AlertsAlertController)

                alert = await controller.создатьРучноеОповещение(alert_data)

                return {
                    "status": "success",
                    "alert_id": alert.id,
                    "message": "Оповещение создано успешно"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Статические файлы
        try:
            import os
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            if os.path.exists(static_dir):
                self.app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
        except Exception as e:
            self.logger.warning(f"Не удалось подключить статические файлы: {e}")

    def _setup_websockets(self):
        """Настройка WebSocket соединений"""

        @self.app.websocket("/ws/updates")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket для обновлений в реальном времени"""
            await websocket.accept()
            client_id = str(id(websocket))
            self.active_connections[client_id] = websocket

            try:
                while True:
                    # Отправка периодических обновлений
                    await asyncio.sleep(30)

                    try:
                        from domain.repositories import WeatherDataRepository
                        repo = self.di_container.разрешить(WeatherDataRepository)
                        latest_data = await repo.get_latest_by_station("26850")

                        if latest_data:
                            update = {
                                "type": "weather_update",
                                "data": WebInterfaceAdapter.prepare_weather_data(latest_data),
                                "timestamp": datetime.now().isoformat()
                            }
                            await websocket.send_json(update)
                    except Exception as e:
                        self.logger.error(f"Ошибка отправки обновления: {e}")

            except WebSocketDisconnect:
                del self.active_connections[client_id]
            except Exception as e:
                self.logger.error(f"Ошибка WebSocket: {e}")
                if client_id in self.active_connections:
                    del self.active_connections[client_id]

    async def start(self):
        """Запуск сервера"""
        from infrastructure.bootstrap import Application_Bootstrap
        config = Application_Bootstrap.get_config()

        host = config.get("services.api_host", "0.0.0.0")
        port = config.get("services.api_port", 8000)

        self.logger.info(f"Запуск API сервера на {host}:{port}")

        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )

        server = uvicorn.Server(config)

        # Запуск в фоновом режиме
        asyncio.create_task(server.serve())

        self.logger.info(f"API сервер запущен: http://{host}:{port}")

        # Бесконечный цикл для поддержания работы
        while True:
            await asyncio.sleep(1)

    async def broadcast_update(self, update_type: str, data: Dict[str, Any]):
        """Трансляция обновления всем подключенным клиентам"""
        if not self.active_connections:
            return

        update = {
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        disconnected = []

        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(update)
            except Exception as e:
                self.logger.error(f"Ошибка отправки клиенту {client_id}: {e}")
                disconnected.append(client_id)

        # Удаление отключенных клиентов
        for client_id in disconnected:
            if client_id in self.active_connections:
                del self.active_connections[client_id]