#!/usr/bin/env python3
"""
Полный скрипт настройки проекта "Образовательный портал"
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Выполнение команды с выводом описания"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} выполнено успешно")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при выполнении: {description}")
        print(f"Код ошибки: {e.returncode}")
        if e.stdout:
            print(f"Вывод: {e.stdout}")
        if e.stderr:
            print(f"Ошибки: {e.stderr}")
        return False

def main():
    """Основная функция настройки"""
    print("🚀 Настройка проекта 'Образовательный портал'")
    print("=" * 50)
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists('requirements.txt'):
        print("❌ Файл requirements.txt не найден. Убедитесь, что вы находитесь в корневой папке проекта.")
        return
    
    # 1. Установка зависимостей
    if not run_command("pip install -r requirements.txt", "Установка зависимостей"):
        print("❌ Не удалось установить зависимости. Проверьте подключение к интернету.")
        return
    
    # 2. Инициализация базы данных
    if not run_command("python init_db.py", "Инициализация базы данных"):
        print("❌ Не удалось инициализировать базу данных.")
        return
    
    # 3. Настройка миграций (опционально)
    print("\n🔄 Настройка миграций...")
    try:
        from app import create_app
        from flask_migrate import init, migrate, upgrade
        from app.models import db
        
        app = create_app()
        with app.app_context():
            # Проверяем, существует ли папка migrations
            migrations_dir = os.path.join(app.root_path, 'migrations')
            if not os.path.exists(migrations_dir):
                init()
                print("✓ Папка миграций создана")
            
            # Создаем и применяем миграцию
            migrate(message="Add reviews table")
            upgrade()
            print("✓ Миграции настроены")
    except Exception as e:
        print(f"⚠️  Предупреждение: Не удалось настроить миграции: {e}")
        print("Вы можете настроить их вручную позже.")
    
    print("\n" + "=" * 50)
    print("🎉 Настройка завершена!")
    print("\nДля запуска приложения выполните:")
    print("  flask run")
    print("\nПриложение будет доступно по адресу: http://127.0.0.1:5000")
    print("\nТестовые данные:")
    print("  Логин: user")
    print("  Пароль: qwerty")
    print("\nДля запуска тестов выполните:")
    print("  pytest tests/")

if __name__ == '__main__':
    main()



