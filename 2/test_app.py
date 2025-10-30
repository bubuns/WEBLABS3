import unittest
from app import app, validate_phone

class FlaskAppTestCase(unittest.TestCase):
    """Тесты для Flask приложения"""
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_page(self):
        """Тест главной страницы"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Лабораторная работа №2', response.data.decode('utf-8'))
    
    def test_url_params_empty(self):
        """Тест страницы URL параметров без параметров"""
        response = self.app.get('/url_params')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Параметры не найдены', response.data.decode('utf-8'))
    
    def test_url_params_with_data(self):
        """Тест страницы URL параметров с данными"""
        response = self.app.get('/url_params?name=John&age=25&city=Moscow')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name', response.data)
        self.assertIn(b'John', response.data)
        self.assertIn(b'age', response.data)
        self.assertIn(b'25', response.data)
        self.assertIn(b'city', response.data)
        self.assertIn(b'Moscow', response.data)
    
    def test_headers_page(self):
        """Тест страницы заголовков запроса"""
        response = self.app.get('/headers')
        self.assertEqual(response.status_code, 200)
        self.assertIn('HTTP Заголовки', response.data.decode('utf-8'))
        self.assertIn('User-Agent', response.data.decode('utf-8'))
    
    def test_cookies_page_empty(self):
        """Тест страницы cookies без cookies"""
        response = self.app.get('/cookies')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Cookie не найдены', response.data.decode('utf-8'))
    
    def test_set_cookie(self):
        """Тест установки cookie"""
        response = self.app.get('/set_cookie/test_cookie/test_value')
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response.location, '/cookies')
    
    def test_delete_cookie(self):
        """Тест удаления cookie"""
        # Сначала устанавливаем cookie
        self.app.get('/set_cookie/test_cookie/test_value')
        # Затем удаляем
        response = self.app.get('/delete_cookie/test_cookie')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/cookies')
    
    def test_form_params_get(self):
        """Тест страницы параметров формы (GET запрос)"""
        response = self.app.get('/form_params')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Тестовая форма', response.data.decode('utf-8'))
    
    def test_form_params_post(self):
        """Тест страницы параметров формы (POST запрос)"""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': '25',
            'city': 'Moscow',
            'message': 'Test message',
            'newsletter': 'yes'
        }
        response = self.app.post('/form_params', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'John Doe', response.data)
        self.assertIn(b'john@example.com', response.data)
        self.assertIn(b'25', response.data)
        self.assertIn(b'Moscow', response.data)
    
    def test_phone_validation_get(self):
        """Тест страницы валидации телефона (GET запрос)"""
        response = self.app.get('/phone_validation')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Валидация номера телефона', response.data.decode('utf-8'))
    
    def test_phone_validation_valid_11_digits_plus7(self):
        """Тест валидации корректного номера с 11 цифрами (+7)"""
        data = {'phone': '+7 (123) 456-75-90'}
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'8-123-456-75-90', response.data)
        self.assertNotIn(b'is-invalid', response.data)
    
    def test_phone_validation_valid_11_digits_8(self):
        """Тест валидации корректного номера с 11 цифрами (8)"""
        data = {'phone': '8(123)4567590'}
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'8-123-456-75-90', response.data)
        self.assertNotIn(b'is-invalid', response.data)
    
    def test_phone_validation_valid_10_digits(self):
        """Тест валидации корректного номера с 10 цифрами"""
        data = {'phone': '123.456.75.90'}
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'8-123-456-75-90', response.data)
        self.assertNotIn(b'is-invalid', response.data)
    
    def test_phone_validation_invalid_wrong_digits_count(self):
        """Тест валидации номера с неверным количеством цифр"""
        data = {'phone': '123456789'}  # 9 цифр
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'is-invalid', response.data)
        self.assertIn('Недопустимый ввод. Неверное количество цифр.', response.data.decode('utf-8'))
    
    def test_phone_validation_invalid_11_digits_wrong_start(self):
        """Тест валидации номера с 11 цифрами, но не начинающегося с 7 или 8"""
        data = {'phone': '12345678901'}  # 11 цифр, но не +7/8
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'is-invalid', response.data)
        self.assertIn('Недопустимый ввод. Неверное количество цифр.', response.data.decode('utf-8'))
    
    def test_phone_validation_invalid_characters(self):
        """Тест валидации номера с недопустимыми символами"""
        data = {'phone': '123abc456'}  # содержит буквы
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'is-invalid', response.data)
        self.assertIn('Недопустимый ввод. В номере телефона встречаются недопустимые символы.', response.data.decode('utf-8'))
    
    def test_phone_validation_empty_input(self):
        """Тест валидации пустого ввода"""
        data = {'phone': ''}
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'is-invalid', response.data)
        self.assertIn('Недопустимый ввод. Неверное количество цифр.', response.data.decode('utf-8'))
    
    def test_phone_validation_with_spaces(self):
        """Тест валидации номера с пробелами"""
        data = {'phone': '8 123 456 75 90'}
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'8-123-456-75-90', response.data)
        self.assertNotIn(b'is-invalid', response.data)
    
    def test_phone_validation_with_dashes(self):
        """Тест валидации номера с дефисами"""
        data = {'phone': '+7-123-456-75-90'}
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'8-123-456-75-90', response.data)
        self.assertNotIn(b'is-invalid', response.data)
    
    def test_phone_validation_with_parentheses(self):
        """Тест валидации номера с круглыми скобками"""
        data = {'phone': '+7 (123) 456-75-90'}
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'8-123-456-75-90', response.data)
        self.assertNotIn(b'is-invalid', response.data)
    
    def test_phone_validation_with_dots(self):
        """Тест валидации номера с точками"""
        data = {'phone': '123.456.75.90'}
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'8-123-456-75-90', response.data)
        self.assertNotIn(b'is-invalid', response.data)
    
    def test_phone_validation_12_digits(self):
        """Тест валидации номера с 12 цифрами"""
        data = {'phone': '123456789012'}  # 12 цифр
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'is-invalid', response.data)
        self.assertIn('Недопустимый ввод. Неверное количество цифр.', response.data.decode('utf-8'))
    
    def test_phone_validation_special_characters(self):
        """Тест валидации номера со специальными символами"""
        data = {'phone': '123@456#789'}  # содержит @ и #
        response = self.app.post('/phone_validation', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'is-invalid', response.data)
        self.assertIn('Недопустимый ввод. В номере телефона встречаются недопустимые символы.', response.data.decode('utf-8'))

class PhoneValidationTestCase(unittest.TestCase):
    """Тесты для функции валидации номера телефона"""
    
    def test_validate_phone_valid_plus7(self):
        """Тест функции валидации с корректным номером +7"""
        result = validate_phone('+7 (123) 456-75-90')
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['formatted'], '8-123-456-75-90')
    
    def test_validate_phone_valid_8(self):
        """Тест функции валидации с корректным номером 8"""
        result = validate_phone('8(123)4567590')
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['formatted'], '8-123-456-75-90')
    
    def test_validate_phone_valid_10_digits(self):
        """Тест функции валидации с корректным номером 10 цифр"""
        result = validate_phone('123.456.75.90')
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['formatted'], '8-123-456-75-90')
    
    def test_validate_phone_invalid_wrong_digits(self):
        """Тест функции валидации с неверным количеством цифр"""
        result = validate_phone('123456789')
        self.assertFalse(result['is_valid'])
        self.assertIn('Неверное количество цифр', result['error'])
    
    def test_validate_phone_invalid_characters(self):
        """Тест функции валидации с недопустимыми символами"""
        result = validate_phone('123abc456')
        self.assertFalse(result['is_valid'])
        self.assertIn('недопустимые символы', result['error'])
    
    def test_validate_phone_empty(self):
        """Тест функции валидации с пустой строкой"""
        result = validate_phone('')
        self.assertFalse(result['is_valid'])
        self.assertIn('Неверное количество цифр', result['error'])

if __name__ == '__main__':
    unittest.main()
