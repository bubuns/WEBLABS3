@echo off
echo Установка зависимостей...
pip install -r requirements.txt

echo.
echo Запуск тестов...
python test_app.py

echo.
echo Запуск приложения...
echo Откройте браузер и перейдите по адресу: http://127.0.0.1:5000
python app.py
