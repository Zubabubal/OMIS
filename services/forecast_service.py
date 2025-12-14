"""
Сервис прогнозирования погоды
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid
import random

from domain.models import Forecast, ModelParameters
from domain.repositories import WeatherDataRepository


class ForecastService:
    """Сервис прогнозирования"""

    def __init__(self, data_repo: WeatherDataRepository):
        self.data_repo = data_repo
        self.logger = logging.getLogger(__name__)

    async def calculate_forecast(self, region: str, params: ModelParameters) -> Forecast:
        """Расчёт прогноза погоды"""
        await asyncio.sleep(0.5)  # Имитация длительного расчёта

        forecast_id = str(uuid.uuid4())
        now = datetime.now()

        # Генерация точек прогноза
        points = []
        for i in range(0, params.forecast_horizon + 1, 3):
            forecast_time = now + timedelta(hours=i)
            points.append({
                "time": forecast_time.strftime("%H:%M"),
                "temperature": 15 + i * 0.1 + (i % 10) - 5,
                "humidity": max(40, 80 - i * 0.5),
                "wind_speed": 5 + (i % 24) * 0.3
            })

        forecast = Forecast(
            id=forecast_id,
            model_type=params.algorithm,
            calculation_time=now,
            valid_from=now,
            valid_to=now + timedelta(hours=params.forecast_horizon),
            region=region,
            points=points
        )

        return forecast

    async def calculate_ensemble(self, region: str, params: ModelParameters,
                                 ensemble_size: int = 5) -> List[Forecast]:
        """Ансамблевый прогноз"""
        tasks = []
        for i in range(ensemble_size):
            ensemble_params = ModelParameters(
                algorithm=params.algorithm,
                initial_conditions=params.initial_conditions,
                grid_resolution=params.grid_resolution,
                forecast_horizon=params.forecast_horizon + (i - ensemble_size // 2)
            )
            tasks.append(self.calculate_forecast(region, ensemble_params))

        return await asyncio.gather(*tasks)

    async def calculate_probabilistic_forecast(self, region: str,
                                               params: ModelParameters,
                                               confidence_level: float = 0.95) -> Dict[str, Any]:
        """Вероятностный прогноз"""
        # Запускаем ансамбль
        ensemble = await self.calculate_ensemble(region, params, ensemble_size=10)

        # Анализируем результаты ансамбля
        temperatures = []
        humidities = []
        wind_speeds = []

        for forecast in ensemble:
            if forecast.points:
                temperatures.append(forecast.points[0].get("temperature", 0))
                humidities.append(forecast.points[0].get("humidity", 0))
                wind_speeds.append(forecast.points[0].get("wind_speed", 0))

        if not temperatures:
            return {"error": "Не удалось рассчитать прогноз"}

        # Рассчитываем статистики
        import statistics

        result = {
            "region": region,
            "confidence_level": confidence_level,
            "ensemble_size": len(ensemble),
            "temperature": {
                "mean": statistics.mean(temperatures),
                "min": min(temperatures),
                "max": max(temperatures),
                "std": statistics.stdev(temperatures) if len(temperatures) > 1 else 0,
                "percentile_10": sorted(temperatures)[int(len(temperatures) * 0.1)],
                "percentile_90": sorted(temperatures)[int(len(temperatures) * 0.9)]
            },
            "humidity": {
                "mean": statistics.mean(humidities),
                "min": min(humidities),
                "max": max(humidities)
            },
            "wind_speed": {
                "mean": statistics.mean(wind_speeds),
                "min": min(wind_speeds),
                "max": max(wind_speeds)
            }
        }

        return result