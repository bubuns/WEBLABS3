import pytest
import tempfile
import os
from app import create_app
from app.models import db


@pytest.fixture
def app():
    """Создание тестового приложения"""
    # Создаем временный файл базы данных
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        
    yield app
    
    # Очистка после тестов
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Тестовый клиент"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Тестовый runner для CLI команд"""
    return app.test_cli_runner()

