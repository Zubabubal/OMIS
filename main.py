"""
Главный файл запуска системы
"""

import asyncio
import sys
from infrastructure.bootstrap import Application_Bootstrap


def main():
    """
    Точка входа в приложение
    """
    print("=" * 60)
    print("СИСТЕМА МОНИТОРИНГА И ПРОГНОЗИРОВАНИЯ ПОГОДЫ")
    print("=" * 60)

    # Запуск системы через Application_Bootstrap
    Application_Bootstrap.main(sys.argv)


if __name__ == "__main__":
    main()