"""
Модели пользователей системы согласно диаграмме
A Пользователь
C Метеоролог
C Климатолог
C ПредставительОтрасли
Метеоролог->(создает)Прогноз
Метеоролог->Пользователь
Климатолог->Пользователь
ПредставительОтрасли->Пользователь
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import hashlib


@dataclass
class Пользователь(ABC):
    """
    A Пользователь
    -ид:String
    -логин:String
    +авторизоваться(пароль:String):Boolean
    """
    ид: str
    логин: str
    _пароль_hash: str
    роль: str
    email: Optional[str] = None
    телефон: Optional[str] = None

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def авторизоваться(self, пароль: str) -> bool:
        """+авторизоваться(пароль:String):Boolean"""
        return self._пароль_hash == self._hash_password(пароль)

    def сменить_пароль(self, старый_пароль: str, новый_пароль: str) -> bool:
        if self.авторизоваться(старый_пароль):
            self._пароль_hash = self._hash_password(новый_пароль)
            return True
        return False

    @abstractmethod
    def доступные_действия(self) -> List[str]:
        pass

    @classmethod
    def создать_пользователя(cls, логин: str, пароль: str, **kwargs):
        return cls(
            ид=f"user_{hashlib.md5(логин.encode()).hexdigest()[:8]}",
            логин=логин,
            _пароль_hash=cls._hash_password(пароль),
            **kwargs
        )


class Метеоролог(Пользователь):
    """
    C Метеоролог
    Метеоролог->Пользователь
    Метеоролог->(создает)Прогноз
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.созданные_прогнозы: List[str] = []

    def доступные_действия(self) -> List[str]:
        return [
            "просмотр_данных",
            "создание_прогноза",
            "редактирование_прогноза",
            "генерация_оповещений",
            "мониторинг_станций"
        ]

    def создать_прогноз(self, прогноз_id: str) -> None:
        """Метеоролог->(создает)Прогноз"""
        self.созданные_прогнозы.append(прогноз_id)

    def получить_статистику(self) -> dict:
        return {
            "логин": self.логин,
            "создано_прогнозов": len(self.созданные_прогнозы),
            "роль": self.роль
        }


class Климатолог(Пользователь):
    """
    C Климатолог
    Климатолог->Пользователь
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.исследования: List[str] = []

    def доступные_действия(self) -> List[str]:
        return [
            "анализ_архива",
            "генерация_отчетов",
            "статистический_анализ",
            "трендовый_анализ",
            "экспорт_данных"
        ]

    def создать_исследование(self, тема: str) -> str:
        research_id = f"research_{len(self.исследования) + 1}"
        self.исследования.append(тема)
        return research_id

    def получить_климатические_данные(self, период_лет: int = 30):
        return {
            "период_лет": период_лет,
            "исследователь": self.логин,
            "доступные_метрики": ["средняя_температура", "осадки", "влажность"]
        }


class ПредставительОтрасли(Пользователь):
    """
    C ПредставительОтрасли
    ПредставительОтрасли->Пользователь
    """

    def __init__(self, отрасль: str, организация: str, **kwargs):
        super().__init__(**kwargs)
        self.отрасль = отрасль
        self.организация = организация
        self.запросы: List[dict] = []

    def доступные_действия(self) -> List[str]:
        base_actions = ["просмотр_прогнозов", "получение_оповещений"]

        if self.отрасль == "МЧС":
            base_actions.extend(["экстренные_оповещения", "карты_рисков"])
        elif self.отрасль == "сельское_хозяйство":
            base_actions.extend(["агропрогнозы", "влажность_почвы"])
        elif self.отрасль == "энергетика":
            base_actions.extend(["прогноз_нагрузки", "ветровая_энергия"])

        return base_actions

    def создать_запрос_прогноза(self, параметры: dict) -> str:
        request_id = f"req_{len(self.запросы) + 1}"
        self.запросы.append({
            "id": request_id,
            "параметры": параметры,
            "отрасль": self.отрасль
        })
        return request_id

    def получить_отраслевой_отчет(self, период: str = "месяц") -> dict:
        return {
            "организация": self.организация,
            "отрасль": self.отрасль,
            "период": период,
            "ключевые_метрики": self._get_industry_metrics()
        }

    def _get_industry_metrics(self) -> List[str]:
        metrics = {
            "МЧС": ["риск_наводнений", "штормовые_предупреждения", "температурные_аномалии"],
            "сельское_хозяйство": ["сумма_температур", "осадки", "влажность_почвы", "заморозки"],
            "энергетика": ["нагрузка_кондиционеров", "ветровая_генерация", "солнечная_радиация"]
        }
        return metrics.get(self.отрасль, [])