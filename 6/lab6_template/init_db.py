#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных и создания тестовых данных
"""

import os
import shutil
import sys
from flask import Flask

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Category, Course, Image, Review

def init_database():
    """Инициализация базы данных"""
    app = create_app()
    
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
        # Создаем категории, если их нет
        first_category = db.session.execute(db.select(Category)).scalars().first()
        if first_category is None:
            categories = [
                Category(name='Программирование'),
                Category(name='Математика'),
                Category(name='Языкознание'),
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("✓ Категории созданы")
        
        # Создаем тестового пользователя, если его нет
        existing_user = db.session.execute(db.select(User).filter_by(login='user')).scalar()
        if existing_user is None:
            user = User(first_name='Иван', last_name='Иванов', login='user')
            user.set_password('qwerty')
            db.session.add(user)
            db.session.commit()
            print("✓ Тестовый пользователь создан (логин: user, пароль: qwerty)")
        
        # Создаем тестовое изображение, если его нет, и кладём файл в media/images
        first_image = db.session.execute(db.select(Image)).scalars().first()
        if first_image is None:
            image = Image(
                id='default_bg',
                file_name='default.jpg',  # используем .jpg, чтобы положить jpeg из static
                mime_type='image/jpeg',
                md5_hash='default_hash'
            )
            db.session.add(image)
            db.session.commit()
            print("✓ Тестовое изображение создано")

        # Гарантируем наличие файла изображения в папке загрузок
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        img_rec = db.session.get(Image, 'default_bg')
        if img_rec is not None:
            dest_path = os.path.join(upload_dir, img_rec.storage_filename)
            if not os.path.exists(dest_path):
                # Для jpg копируем готовый jpeg из static
                ext = os.path.splitext(img_rec.file_name)[1].lower()
                if ext in ('.jpg', '.jpeg'):
                    src_path = os.path.join(app.root_path, 'static', 'images', 'default-profile-picture-300x300.jpeg')
                else:
                    src_path = os.path.join(app.root_path, 'static', 'images', 'polytech_logo.png')
                try:
                    shutil.copyfile(src_path, dest_path)
                except FileNotFoundError:
                    # В крайнем случае просто создадим пустой файл-заглушку
                    open(dest_path, 'ab').close()
        
        # Создаем тестовый курс, если его нет
        first_course = db.session.execute(db.select(Course)).scalars().first()
        if first_course is None:
            # Получаем реальные id категории и пользователя
            any_category = db.session.execute(db.select(Category)).scalars().first()
            any_user = db.session.execute(db.select(User)).scalars().first()
            course = Course(
                name='Основы Python',
                short_desc='Изучение основ программирования на Python',
                full_desc='Этот курс познакомит вас с основами программирования на языке Python. Вы изучите синтаксис, типы данных, функции, классы и многое другое.',
                category_id=any_category.id,
                author_id=any_user.id,
                background_image_id='default_bg'
            )
            db.session.add(course)
            db.session.commit()
            print("✓ Тестовый курс создан")
        
        print("\n🎉 База данных успешно инициализирована!")
        print("Для запуска приложения выполните: flask run")

if __name__ == '__main__':
    init_database()

