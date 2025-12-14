"""
ForecastController из диаграммы контроллеров
C ForecastController
+calculateForecast(region: String, params: ModelParameters): Forecast
+getLatestForecast(region: String): Forecast
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid

from domain.models import Forecast, Прогноз, ModelParameters
from domain.repositories import ForecastRepository
from services.forecast_service import ForecastService


class ForecastController:
    """Контроллер управления прогнозами"""

    def __init__(self, forecast_service: ForecastService,
                 forecast_repository: ForecastRepository):
        self.forecast_service = forecast_service
        self.forecast_repository = forecast_repository
        self.logger = logging.getLogger(__name__)

    async def calculate_forecast(self, region: str,
                                 params: ModelParameters) -> Forecast:
        """+calculateForecast(region: String, params: ModelParameters): Forecast"""
        self.logger.info(f"Расчет прогноза для региона {region}")

        # Расчет прогноза через сервис
        forecast = await self.forecast_service.calculate_forecast(region, params)

        # Сохранение в репозиторий
        await self.forecast_repository.save(forecast)

        self.logger.info(f"Прогноз {forecast.id} сохранен")
        return forecast

    async def get_latest_forecast(self, region: str) -> Optional[Forecast]:
        """+getLatestForecast(region: String): Forecast"""
        forecast = await self.forecast_repository.get_latest_for_region(region)

        if forecast:
            self.logger.info(f"Получен прогноз {forecast.id} для региона {region}")
        else:
            self.logger.info(f"Прогнозы для региона {region} не найдены")

        return forecast

    async def calculate_ensemble_forecast(self, region: str,
                                          params: ModelParameters,
                                          ensemble_size: int = 5) -> List[Forecast]:
        """Расчет ансамблевого прогноза"""
        self.logger.info(f"Расчет ансамблевого прогноза для региона {region}")

        forecasts = await self.forecast_service.calculate_ensemble(
            region, params, ensemble_size
        )

        # Сохранение всех прогнозов ансамбля
        for forecast in forecasts:
            await self.forecast_repository.save(forecast)

        self.logger.info(f"Ансамблевый прогноз сохранен: {len(forecasts)} членов")
        return forecasts

    async def get_forecast_statistics(self, region: str) -> Dict[str, Any]:
        """Статистика прогнозов для региона"""
        forecasts = await self.forecast_repository.get_all_for_region(region)

        if not forecasts:
            return {"region": region, "forecast_count": 0}

        latest = max(forecasts, key=lambda x: x.calculation_time)
        models_used = list(set(f.model_type for f in forecasts))

        return {
            "region": region,
            "forecast_count": len(forecasts),
            "latest_forecast_id": latest.id,
            "latest_model": latest.model_type,
            "models_used": models_used,
            "first_forecast_date": min(f.calculation_time for f in forecasts).isoformat(),
            "last_forecast_date": latest.calculation_time.isoformat()
        }

    async def verify_forecast_accuracy(self, forecast_id: str) -> Dict[str, Any]:
        """Верификация точности прогноза"""
        forecast = await self.forecast_repository.get_by_id(forecast_id)
        if not forecast:
            return {"error": "Прогноз не найден"}

        # Здесь была бы логика сравнения с фактическими данными
        # В этом примере возвращаем тестовые данные
        return {
            "forecast_id": forecast_id,
            "temperature_accuracy": 0.85,
            "precipitation_accuracy": 0.72,
            "wind_accuracy": 0.68,
            "overall_accuracy": 0.75,
            "verification_date": datetime.now().isoformat()
        }