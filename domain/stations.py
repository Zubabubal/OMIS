"""
Модели метеостанций
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from .models import GeoPoint, Метеостанция


@dataclass
class StationNetwork:
    """Сеть метеостанций"""
    id: str
    name: str
    stations: List[Метеостанция] = field(default_factory=list)
    coverage_area: Dict[str, Any] = field(default_factory=dict)

    def add_station(self, station: Метеостанция) -> None:
        self.stations.append(station)

    def get_active_stations(self) -> List[Метеостанция]:
        return [s for s in self.stations if s.статус == "активна"]

    def get_station_by_id(self, station_id: str) -> Метеостанция:
        for station in self.stations:
            if station.идСтанции == station_id:
                return station
        raise ValueError(f"Станция {station_id} не найдена")

    def calculate_coverage(self) -> Dict[str, Any]:
        if not self.stations:
            return {"area_km2": 0, "stations_count": 0}

        active_count = len(self.get_active_stations())
        return {
            "area_km2": active_count * 100,  # Упрощенный расчет
            "stations_count": len(self.stations),
            "active_stations": active_count,
            "coverage_percentage": (active_count / len(self.stations)) * 100
        }