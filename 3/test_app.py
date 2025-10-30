import unittest
import os
import sys
from app import app, users, User
from werkzeug.security import check_password_hash

class FlaskAppTestCase(unittest.TestCase):
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Очистка после тестов"""
        self.app_context.pop()
    
    def test_1_home_page_loads(self):
        """Тест 1: Главная страница загружается корректно"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Добро пожаловать!', response.get_data(as_text=True))
    
    def test_2_counter_page_increments(self):
        """Тест 2: Счетчик посещений работает корректно и для каждого пользователя выводит своё значение"""
        # Первое посещение
        response1 = self.client.get('/counter')
        self.assertEqual(response1.status_code, 200)
        self.assertIn('1', response1.get_data(as_text=True))
        
        # Второе посещение
        response2 = self.client.get('/counter')
        self.assertEqual(response2.status_code, 200)
        self.assertIn('2', response2.get_data(as_text=True))
        
        # Третье посещение
        response3 = self.client.get('/counter')
        self.assertEqual(response3.status_code, 200)
        self.assertIn('3', response3.get_data(as_text=True))
    
    def test_3_login_page_loads(self):
        """Тест 3: Страница входа загружается корректно"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход в систему', response.get_data(as_text=True))
        self.assertIn('Запомнить меня', response.get_data(as_text=True))
    
    def test_4_successful_login_redirects_to_home(self):
        """Тест 4: После успешной аутентификации пользователь перенаправляется на главную страницу"""
        response = self.client.post('/login', data={
            'username': 'user',
            'password': 'qwerty'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вы успешно вошли в систему!', response.get_data(as_text=True))
        self.assertIn('Добро пожаловать!', response.get_data(as_text=True))
    
    def test_5_failed_login_stays_on_login_page(self):
        """Тест 5: После неудачной попытки аутентификации пользователь остается на той же странице"""
        response = self.client.post('/login', data={
            'username': 'user',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Неверное имя пользователя или пароль!', response.get_data(as_text=True))
        self.assertIn('Вход в систему', response.get_data(as_text=True))
    
    def test_6_authenticated_user_accesses_secret_page(self):
        """Тест 6: Аутентифицированный пользователь имеет доступ к секретной странице"""
        # Логинимся
        self.client.post('/login', data={
            'username': 'user',
            'password': 'qwerty'
        })
        
        # Пытаемся получить доступ к секретной странице
        response = self.client.get('/secret')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Секретная страница', response.get_data(as_text=True))
        self.assertIn('Доступ разрешен!', response.get_data(as_text=True))
    
    def test_7_unauthenticated_user_redirected_to_login(self):
        """Тест 7: Неаутентифицированный пользователь при попытке доступа к секретной странице перенаправляется на страницу аутентификации"""
        response = self.client.get('/secret', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход в систему', response.get_data(as_text=True))
        self.assertIn('Для доступа к запрашиваемой странице необходимо пройти процедуру аутентификации', response.get_data(as_text=True))
    
    def test_8_login_after_redirect_goes_to_secret_page(self):
        """Тест 8: При аутентификации после неудачной попытки доступа к секретной странице пользователь автоматически перенаправляется на секретную страницу"""
        # Пытаемся получить доступ к секретной странице без авторизации
        response1 = self.client.get('/secret')
        self.assertEqual(response1.status_code, 302)  # Редирект
        
        # Получаем URL для входа с параметром next
        login_url = response1.location
        self.assertIn('/login?next=', login_url)
        
        # Логинимся, следуя редиректу
        response2 = self.client.post(login_url, data={
            'username': 'user',
            'password': 'qwerty'
        }, follow_redirects=True)
        
        self.assertEqual(response2.status_code, 200)
        self.assertIn('Секретная страница', response2.get_data(as_text=True))
        self.assertIn('Доступ разрешен!', response2.get_data(as_text=True))
    
    def test_9_remember_me_functionality(self):
        """Тест 9: Параметр 'Запомнить меня' работает корректно"""
        # Логинимся с включенным "Запомнить меня"
        response = self.client.post('/login', data={
            'username': 'user',
            'password': 'qwerty',
            'remember': 'on'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вы успешно вошли в систему!', response.get_data(as_text=True))
        
        # Проверяем, что пользователь остается авторизованным
        response2 = self.client.get('/secret')
        self.assertEqual(response2.status_code, 200)
        self.assertIn('Секретная страница', response2.get_data(as_text=True))
    
    def test_10_navbar_links_visibility(self):
        """Тест 10: В навбаре корректно показываются/скрываются ссылки в зависимости от статуса пользователя"""
        # Без авторизации
        response1 = self.client.get('/')
        self.assertEqual(response1.status_code, 200)
        self.assertIn('Войти', response1.get_data(as_text=True))
        self.assertNotIn('Секретная страница', response1.get_data(as_text=True))
        self.assertNotIn('Выйти', response1.get_data(as_text=True))
        
        # С авторизацией
        self.client.post('/login', data={
            'username': 'user',
            'password': 'qwerty'
        })
        
        response2 = self.client.get('/')
        self.assertEqual(response2.status_code, 200)
        self.assertIn('Секретная страница', response2.get_data(as_text=True))
        self.assertIn('Выйти', response2.get_data(as_text=True))
        self.assertNotIn('Войти', response2.get_data(as_text=True))
    
    def test_11_logout_functionality(self):
        """Тест 11: Функция выхода работает корректно"""
        # Логинимся
        self.client.post('/login', data={
            'username': 'user',
            'password': 'qwerty'
        })
        
        # Проверяем, что можем получить доступ к секретной странице
        response1 = self.client.get('/secret')
        self.assertEqual(response1.status_code, 200)
        
        # Выходим
        response2 = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn('Вы вышли из системы!', response2.get_data(as_text=True))
        
        # Проверяем, что больше не можем получить доступ к секретной странице
        response3 = self.client.get('/secret', follow_redirects=True)
        self.assertEqual(response3.status_code, 200)
        self.assertIn('Вход в систему', response3.get_data(as_text=True))
    
    def test_12_user_data_display(self):
        """Тест 12: На секретной странице корректно отображается информация о пользователе"""
        # Логинимся
        self.client.post('/login', data={
            'username': 'user',
            'password': 'qwerty'
        })
        
        # Проверяем отображение данных пользователя на секретной странице
        response = self.client.get('/secret')
        self.assertEqual(response.status_code, 200)
        self.assertIn('user', response.get_data(as_text=True))  # Имя пользователя
        self.assertIn('1', response.get_data(as_text=True))     # ID пользователя

if __name__ == '__main__':
    unittest.main()