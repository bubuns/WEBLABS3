#!/usr/bin/env python3
"""
Скрипт для настройки миграций Flask-Migrate
"""

import os
import sys
from flask import Flask
from flask_migrate import init, migrate, upgrade

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def setup_migrations():
    """Настройка миграций"""
    app = create_app()
    
    with app.app_context():
        # Проверяем, существует ли папка migrations
        migrations_dir = os.path.join(app.root_path, 'migrations')
        if not os.path.exists(migrations_dir):
            print("Инициализация папки миграций...")
            init()
            print("✓ Папка миграций создана")
        
        # Создаем миграцию
        print("Создание миграции...")
        migrate(message="Add reviews table")
        print("✓ Миграция создана")
        
        # Применяем миграцию
        print("Применение миграции...")
        upgrade()
        print("✓ Миграция применена")
        
        print("\n🎉 Миграции успешно настроены!")

if __name__ == '__main__':
    setup_migrations()



