"""
DI_Container из диаграммы
C DI_Cntainer <<Dependency Ingection>>
-registry:Map<Interface,Object>
+заргестрировать(интерфес:Class, реалзаия: Class):void
+разрешить(интерфейс: Class): Object
"""

import inspect
from typing import Dict, Type, Any, Callable, Union, List


class DI_Container:
    """Контейнер внедрения зависимостей"""

    def __init__(self):
        self._registry: Dict[Type, Union[Type, Callable, Any]] = {}
        self._instances: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}

    def зарегистрировать(self, interface: Type, implementation: Union[Type, Callable, Any],
                         is_instance: bool = False, is_singleton: bool = True) -> None:
        """
        +зарегистрировать(интерфес:Class, реализация: Class):void

        Args:
            interface: Тип интерфейса или класса
            implementation: Класс реализации или фабричная функция
            is_instance: Если True, implementation - уже созданный экземпляр
            is_singleton: Если True, создается один экземпляр на все время жизни
        """
        if is_instance:
            self._instances[interface] = implementation
            if is_singleton:
                self._singletons[interface] = implementation
        else:
            self._registry[interface] = (implementation, is_singleton)

        # Исправляем вывод для встроенных типов
        interface_name = getattr(interface, '__name__', str(interface))
        if callable(implementation) and hasattr(implementation, '__name__'):
            impl_name = implementation.__name__
        else:
            impl_name = str(type(implementation).__name__)

        print(f"DI: Зарегистрирован {interface_name} -> {impl_name}")

    def разрешить(self, interface: Type) -> Any:
        """+разрешить(интерфейс: Class): Object"""
        # Проверяем, есть ли уже созданный экземпляр синглтона
        if interface in self._singletons:
            return self._singletons[interface]

        # Проверяем, есть ли уже созданный экземпляр
        if interface in self._instances:
            return self._instances[interface]

        # Проверяем, есть ли регистрация
        if interface not in self._registry:
            # Пытаемся создать экземпляр напрямую
            if inspect.isclass(interface):
                try:
                    instance = self._create_instance(interface)
                    self._instances[interface] = instance
                    return instance
                except Exception as e:
                    raise ValueError(
                        f"Интерфейс {interface.__name__} не зарегистрирован "
                        f"и не может быть создан напрямую: {e}"
                    ) from e
            else:
                raise ValueError(f"Интерфейс {interface.__name__} не зарегистрирован в DI контейнере")

        implementation, is_singleton = self._registry[interface]

        # Если implementation - это функция (фабрика)
        if callable(implementation) and not inspect.isclass(implementation):
            instance = implementation()
            if is_singleton:
                self._singletons[interface] = instance
            else:
                self._instances[interface] = instance
            return instance

        # Если implementation - это класс
        if inspect.isclass(implementation):
            instance = self._create_instance(implementation)
            if is_singleton:
                self._singletons[interface] = instance
            else:
                self._instances[interface] = instance
            return instance

        # Если implementation - это уже что-то готовое
        if is_singleton:
            self._singletons[interface] = implementation
        else:
            self._instances[interface] = implementation
        return implementation

    def _create_instance(self, implementation: Type) -> Any:
        """Создание экземпляра с внедрением зависимостей"""
        constructor = implementation.__init__
        signature = inspect.signature(constructor)
        parameters = []

        # Анализируем параметры конструктора (пропускаем self)
        for param_name, param in list(signature.parameters.items())[1:]:
            param_type = param.annotation

            if param_type == inspect.Parameter.empty:
                # Пытаемся создать с параметром по умолчанию
                if param.default != inspect.Parameter.empty:
                    parameters.append(param.default)
                else:
                    raise ValueError(
                        f"Не указан тип параметра {param_name} "
                        f"в классе {implementation.__name__}"
                    )
            else:
                try:
                    dependency = self.разрешить(param_type)
                    parameters.append(dependency)
                except ValueError as e:
                    # Если зависимость не зарегистрирована, используем значение по умолчанию
                    if param.default != inspect.Parameter.empty:
                        parameters.append(param.default)
                    else:
                        raise ValueError(
                            f"Не удалось разрешить зависимость {param_type.__name__} "
                            f"для параметра {param_name} в классе {implementation.__name__}"
                        ) from e

        # Создаем экземпляр
        return implementation(*parameters)

    def clear(self) -> None:
        """Очистка контейнера"""
        self._registry.clear()
        self._instances.clear()
        self._singletons.clear()

    def get_registered_types(self) -> List[Type]:
        """Получить все зарегистрированные типы"""
        return list(self._registry.keys())

    def get_singleton_instances(self) -> Dict[Type, Any]:
        """Получить все синглтон экземпляры"""
        return self._singletons.copy()