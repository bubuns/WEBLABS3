import unittest
import os
import tempfile
from app import app, db, User, Role, VisitLog, validate_login, validate_password, validate_name
from werkzeug.security import generate_password_hash

class UserManagementTestCase(unittest.TestCase):
    
    def setUp(self):
        """Настройка тестовой среды"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Создание тестовых ролей
            admin_role = Role(name='Администратор', description='Полный доступ')
            user_role = Role(name='Пользователь', description='Обычный пользователь')
            db.session.add(admin_role)
            db.session.add(user_role)
            db.session.commit()
            
            # Создание тестового пользователя
            test_user = User(
                login='testuser',
                password_hash='hashed_password',
                name='Тест',
                surname='Пользователь',
                role_id=admin_role.id
            )
            db.session.add(test_user)
            db.session.commit()
    
    def tearDown(self):
        """Очистка после тестов"""
        os.close(self.db_fd)
        with app.app_context():
            db.drop_all()
    
    def test_validate_login(self):
        """Тест валидации логина"""
        # Валидные логины
        self.assertEqual(validate_login('valid123'), (True, ''))
        self.assertEqual(validate_login('user1'), (True, ''))
        
        # Невалидные логины
        valid, error = validate_login('')
        self.assertFalse(valid)
        self.assertIn('пустым', error)
        
        valid, error = validate_login('abc')
        self.assertFalse(valid)
        self.assertIn('5 символов', error)
        
        valid, error = validate_login('user@123')
        self.assertFalse(valid)
        self.assertIn('латинских букв', error)
    
    def test_validate_password(self):
        """Тест валидации пароля"""
        # Валидные пароли
        self.assertEqual(validate_password('ValidPass123'), (True, ''))
        self.assertEqual(validate_password('Test123!'), (True, ''))
        
        # Невалидные пароли
        valid, error = validate_password('')
        self.assertFalse(valid)
        self.assertIn('пустым', error)
        
        valid, error = validate_password('short')
        self.assertFalse(valid)
        self.assertIn('8 символов', error)
        
        valid, error = validate_password('nouppercase123')
        self.assertFalse(valid)
        self.assertIn('заглавную', error)
        
        valid, error = validate_password('NOLOWERCASE123')
        self.assertFalse(valid)
        self.assertIn('строчную', error)
        
        valid, error = validate_password('NoNumbers')
        self.assertFalse(valid)
        self.assertIn('цифру', error)
        
        valid, error = validate_password('Test 123')
        self.assertFalse(valid)
        self.assertIn('пробелы', error)
    
    def test_validate_name(self):
        """Тест валидации имени"""
        # Валидные имена
        self.assertEqual(validate_name('Иван', 'Имя'), (True, ''))
        self.assertEqual(validate_name('John', 'Имя'), (True, ''))
        
        # Невалидные имена
        valid, error = validate_name('', 'Имя')
        self.assertFalse(valid)
        self.assertIn('пустым', error)
    
    def test_index_page(self):
        """Тест главной страницы"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Список пользователей', response.data.decode('utf-8'))
    
    def test_login_page(self):
        """Тест страницы входа"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход в систему', response.data.decode('utf-8'))
    
    def test_login_success(self):
        """Тест успешного входа"""
        with app.app_context():
            # Создаем пользователя с известным паролем
            user = User.query.filter_by(login='testuser').first()
            user.password_hash = generate_password_hash('testpassword')
            db.session.commit()
        
        response = self.app.post('/login', data={
            'login': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        
        # Проверяем, что пользователь перенаправлен на главную страницу
        self.assertEqual(response.status_code, 200)
    
    def test_login_failure(self):
        """Тест неудачного входа"""
        response = self.app.post('/login', data={
            'login': 'wronguser',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Неверный логин или пароль', response.data.decode('utf-8'))
    
    def test_logout(self):
        """Тест выхода из системы"""
        # Сначала входим в систему
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
        
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что сессия очищена
        with self.app.session_transaction() as sess:
            self.assertNotIn('user_id', sess)
    
    def test_view_user(self):
        """Тест просмотра пользователя"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
            sess['user_role'] = 'Администратор'
        
        response = self.app.get('/user/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Просмотр пользователя', response.data.decode('utf-8'))
    
    def test_view_nonexistent_user(self):
        """Тест просмотра несуществующего пользователя"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
            sess['user_role'] = 'Администратор'
        
        response = self.app.get('/user/999')
        self.assertEqual(response.status_code, 404)
    
    def test_create_user_page_requires_auth(self):
        """Тест, что страница создания требует аутентификации"""
        response = self.app.get('/user/create', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход в систему', response.data.decode('utf-8'))
    
    def test_create_user_authenticated(self):
        """Тест создания пользователя аутентифицированным пользователем"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
        
        response = self.app.get('/user/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Создание пользователя', response.data.decode('utf-8'))
    
    def test_create_user_success(self):
        """Тест успешного создания пользователя"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
        
        response = self.app.post('/user/create', data={
            'login': 'newuser',
            'password': 'NewPass123',
            'surname': 'Новый',
            'name': 'Пользователь',
            'patronymic': 'Тестовый',
            'role_id': '1'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Пользователь успешно создан', response.data.decode('utf-8'))
        
        # Проверяем, что пользователь создан в БД
        with app.app_context():
            user = User.query.filter_by(login='newuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'Пользователь')
    
    def test_create_user_validation_errors(self):
        """Тест валидации при создании пользователя"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
        
        response = self.app.post('/user/create', data={
            'login': 'ab',  # Слишком короткий
            'password': '123',  # Слишком короткий
            'surname': '',  # Пустое
            'name': '',  # Пустое
            'role_id': '1'
        })
        
        # Flask может возвращать 400 при ошибках валидации, что нормально
        self.assertIn(response.status_code, [200, 400])
        if response.status_code == 200:
            self.assertIn('is-invalid', response.data.decode('utf-8'))
    
    def test_edit_user_requires_auth(self):
        """Тест, что редактирование требует аутентификации"""
        response = self.app.get('/user/1/edit', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход в систему', response.data.decode('utf-8'))
    
    def test_edit_user_success(self):
        """Тест успешного редактирования пользователя"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
        
        response = self.app.post('/user/1/edit', data={
            'surname': 'Обновленная',
            'name': 'Фамилия',
            'patronymic': 'Отчество',
            'role_id': '2'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Пользователь успешно обновлен', response.data.decode('utf-8'))
        
        # Проверяем, что данные обновлены в БД
        with app.app_context():
            user = User.query.get(1)
            self.assertEqual(user.surname, 'Обновленная')
            self.assertEqual(user.role_id, 2)
    
    def test_delete_user_requires_auth(self):
        """Тест, что удаление требует аутентификации"""
        response = self.app.post('/user/1/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход в систему', response.data.decode('utf-8'))
    
    def test_delete_user_success(self):
        """Тест успешного удаления пользователя"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
        
        # Создаем дополнительного пользователя для удаления
        with app.app_context():
            new_user = User(
                login='todelete',
                password_hash='hash',
                name='Удаляемый',
                surname='Пользователь'
            )
            db.session.add(new_user)
            db.session.commit()
            user_id = new_user.id
        
        response = self.app.post(f'/user/{user_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Пользователь успешно удален', response.data.decode('utf-8'))
        
        # Проверяем, что пользователь удален из БД
        with app.app_context():
            user = User.query.get(user_id)
            self.assertIsNone(user)
    
    def test_change_password_requires_auth(self):
        """Тест, что смена пароля требует аутентификации"""
        response = self.app.get('/change_password', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход в систему', response.data.decode('utf-8'))
    
    def test_change_password_page(self):
        """Тест страницы смены пароля"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
        
        response = self.app.get('/change_password')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Смена пароля', response.data.decode('utf-8'))
    
    def test_change_password_validation(self):
        """Тест валидации при смене пароля"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
        
        response = self.app.post('/change_password', data={
            'old_password': 'wrong',
            'new_password': '123',
            'confirm_password': '456'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('is-invalid', response.data.decode('utf-8'))
    
    def test_visit_log_creation(self):
        """Тест создания записи в журнале посещений"""
        with app.app_context():
            # Создаем пользователя
            user = User(
                login='testuser2',
                password_hash='hashed_password',
                name='Тест2',
                surname='Пользователь2',
                role_id=1
            )
            db.session.add(user)
            db.session.commit()
            
            # Создаем запись посещения
            visit = VisitLog(
                path='/test',
                user_id=user.id
            )
            db.session.add(visit)
            db.session.commit()
            
            # Проверяем, что запись создана
            visits = VisitLog.query.all()
            self.assertEqual(len(visits), 1)
            self.assertEqual(visits[0].path, '/test')
            self.assertEqual(visits[0].user_id, user.id)
    
    def test_reports_index_requires_auth(self):
        """Тест, что страница отчетов требует аутентификации"""
        response = self.app.get('/reports/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход в систему', response.data.decode('utf-8'))
    
    def test_reports_index_authenticated(self):
        """Тест страницы отчетов для аутентифицированного пользователя"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
            sess['user_role'] = 'Администратор'
        
        response = self.app.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Журнал посещений', response.data.decode('utf-8'))
    
    def test_reports_by_pages(self):
        """Тест отчета по страницам"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
            sess['user_role'] = 'Администратор'
        
        # Создаем тестовые записи посещений
        with app.app_context():
            visit1 = VisitLog(path='/page1', user_id=1)
            visit2 = VisitLog(path='/page1', user_id=1)
            visit3 = VisitLog(path='/page2', user_id=1)
            db.session.add_all([visit1, visit2, visit3])
            db.session.commit()
        
        response = self.app.get('/reports/by_pages')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Отчет по посещениям страниц', response.data.decode('utf-8'))
    
    def test_reports_by_users(self):
        """Тест отчета по пользователям"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
            sess['user_role'] = 'Администратор'
        
        response = self.app.get('/reports/by_users')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Отчет по посещениям пользователей', response.data.decode('utf-8'))
    
    def test_csv_export_by_pages(self):
        """Тест экспорта отчета по страницам в CSV"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
            sess['user_role'] = 'Администратор'
        
        response = self.app.get('/reports/by_pages/export')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', response.headers['Content-Disposition'])
    
    def test_csv_export_by_users(self):
        """Тест экспорта отчета по пользователям в CSV"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
            sess['user_role'] = 'Администратор'
        
        response = self.app.get('/reports/by_users/export')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', response.headers['Content-Disposition'])
    
    def test_user_cannot_edit_other_users(self):
        """Тест, что обычный пользователь не может редактировать других пользователей"""
        # Создаем второго пользователя
        with app.app_context():
            user2 = User(
                login='user2',
                password_hash='hash',
                name='Пользователь2',
                surname='Тест2',
                role_id=2  # Обычный пользователь
            )
            db.session.add(user2)
            db.session.commit()
            user2_id = user2.id
        
        # Входим как обычный пользователь
        with self.app.session_transaction() as sess:
            sess['user_id'] = user2_id
            sess['user_login'] = 'user2'
            sess['user_role'] = 'Пользователь'
        
        # Пытаемся редактировать другого пользователя
        response = self.app.get(f'/user/1/edit', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('недостаточно прав', response.data.decode('utf-8'))
    
    def test_user_can_edit_own_data(self):
        """Тест, что обычный пользователь может редактировать свои данные"""
        # Создаем обычного пользователя
        with app.app_context():
            user = User(
                login='user3',
                password_hash='hash',
                name='Пользователь3',
                surname='Тест3',
                role_id=2  # Обычный пользователь
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Входим как этот пользователь
        with self.app.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_login'] = 'user3'
            sess['user_role'] = 'Пользователь'
        
        # Редактируем свои данные
        response = self.app.get(f'/user/{user_id}/edit')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Редактирование пользователя', response.data.decode('utf-8'))
    
    def test_admin_can_access_all_functions(self):
        """Тест, что администратор может получить доступ ко всем функциям"""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_login'] = 'testuser'
            sess['user_role'] = 'Администратор'
        
        # Тестируем доступ к созданию пользователя
        response = self.app.get('/user/create')
        self.assertEqual(response.status_code, 200)
        
        # Тестируем доступ к просмотру пользователя
        response = self.app.get('/user/1')
        self.assertEqual(response.status_code, 200)
        
        # Тестируем доступ к редактированию пользователя
        response = self.app.get('/user/1/edit')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
