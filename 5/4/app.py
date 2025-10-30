from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модели базы данных
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    users = db.relationship('User', backref='role', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(50))
    name = db.Column(db.String(50), nullable=False)
    patronymic = db.Column(db.String(50))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VisitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='visit_logs')

# Функции валидации
def validate_login(login):
    if not login:
        return False, "Поле не может быть пустым"
    if len(login) < 5:
        return False, "Логин должен содержать не менее 5 символов"
    if not re.match(r'^[a-zA-Z0-9]+$', login):
        return False, "Логин должен состоять только из латинских букв и цифр"
    return True, ""

def validate_password(password):
    if not password:
        return False, "Поле не может быть пустым"
    if len(password) < 8:
        return False, "Пароль должен содержать не менее 8 символов"
    if len(password) > 128:
        return False, "Пароль должен содержать не более 128 символов"
    if ' ' in password:
        return False, "Пароль не должен содержать пробелы"
    if not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"
    if not re.search(r'[a-z]', password):
        return False, "Пароль должен содержать хотя бы одну строчную букву"
    if not re.search(r'[0-9]', password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    if not re.match(r'^[a-zA-Zа-яА-Я0-9~!?@#$%^&*_\-+()\[\]{}></\\|"\'.,:;]+$', password):
        return False, "Пароль содержит недопустимые символы"
    return True, ""

def validate_name(name, field_name):
    if not name:
        return False, f"Поле {field_name} не может быть пустым"
    return True, ""

# Декоратор для проверки аутентификации
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Необходимо войти в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Декоратор для проверки прав доступа
def check_rights(required_rights):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Необходимо войти в систему', 'error')
                return redirect(url_for('login'))
            
            user = User.query.get(session['user_id'])
            if not user or not user.role:
                flash('У вас недостаточно прав для доступа к данной странице.', 'error')
                return redirect(url_for('index'))
            
            # Проверяем права администратора
            if user.role.name == 'Администратор':
                # Администратор имеет все права
                return f(*args, **kwargs)
            
            # Проверяем права обычного пользователя
            if user.role.name == 'Пользователь':
                if 'edit_own_data' in required_rights:
                    # Пользователь может редактировать только свои данные
                    if 'user_id' in kwargs and kwargs['user_id'] != user.id:
                        flash('У вас недостаточно прав для доступа к данной странице.', 'error')
                        return redirect(url_for('index'))
                    return f(*args, **kwargs)
                elif 'view_own_profile' in required_rights:
                    # Пользователь может просматривать только свой профиль
                    if 'user_id' in kwargs and kwargs['user_id'] != user.id:
                        flash('У вас недостаточно прав для доступа к данной странице.', 'error')
                        return redirect(url_for('index'))
                    return f(*args, **kwargs)
                elif 'view_own_visits' in required_rights:
                    return f(*args, **kwargs)
            
            flash('У вас недостаточно прав для доступа к данной странице.', 'error')
            return redirect(url_for('index'))
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# Декоратор для логирования посещений
@app.before_request
def log_visit():
    # Исключаем статические файлы и некоторые служебные маршруты
    if request.endpoint and not request.endpoint.startswith('static'):
        user_id = session.get('user_id') if 'user_id' in session else None
        visit_log = VisitLog(
            path=request.path,
            user_id=user_id
        )
        db.session.add(visit_log)
        db.session.commit()

# Маршруты
@app.route('/')
def index():
    users = User.query.all()
    user_role = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.role:
            user_role = user.role.name
            session['user_role'] = user_role
    return render_template('index.html', users=users, is_authenticated='user_id' in session)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        
        user = User.query.filter_by(login=login).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_login'] = user.login
            if user.role:
                session['user_role'] = user.role.name
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/user/<int:user_id>')
@check_rights(['view_own_profile'])
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('view_user.html', user=user)

@app.route('/user/create', methods=['GET', 'POST'])
@check_rights(['create_users'])
def create_user():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        surname = request.form['surname']
        name = request.form['name']
        patronymic = request.form['patronymic']
        role_id = request.form.get('role_id')
        
        errors = {}
        
        # Валидация
        login_valid, login_error = validate_login(login)
        if not login_valid:
            errors['login'] = login_error
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            errors['password'] = password_error
        
        name_valid, name_error = validate_name(name, 'Имя')
        if not name_valid:
            errors['name'] = name_error
        
        surname_valid, surname_error = validate_name(surname, 'Фамилия')
        if not surname_valid:
            errors['surname'] = surname_error
        
        # Проверка уникальности логина
        if User.query.filter_by(login=login).first():
            errors['login'] = "Пользователь с таким логином уже существует"
        
        if errors:
            roles = Role.query.all()
            return render_template('user_form.html', 
                                 errors=errors, 
                                 form_data=request.form, 
                                 roles=roles,
                                 is_edit=False)
        
        try:
            user = User(
                login=login,
                password_hash=generate_password_hash(password),
                surname=surname,
                name=name,
                patronymic=patronymic,
                role_id=role_id if role_id else None
            )
            db.session.add(user)
            db.session.commit()
            flash('Пользователь успешно создан', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при создании пользователя', 'error')
            roles = Role.query.all()
            return render_template('user_form.html', 
                                 errors={'general': 'Ошибка при создании пользователя'}, 
                                 form_data=request.form, 
                                 roles=roles,
                                 is_edit=False)
    
    roles = Role.query.all()
    return render_template('user_form.html', roles=roles, is_edit=False)

@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@check_rights(['edit_own_data'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        surname = request.form['surname']
        name = request.form['name']
        patronymic = request.form['patronymic']
        role_id = request.form.get('role_id')
        
        # Если пользователь - обычный пользователь, не изменяем роль
        current_user = User.query.get(session['user_id'])
        if current_user and current_user.role and current_user.role.name == 'Пользователь' and current_user.id == user.id:
            role_id = user.role_id  # Сохраняем текущую роль
        
        errors = {}
        
        # Валидация
        name_valid, name_error = validate_name(name, 'Имя')
        if not name_valid:
            errors['name'] = name_error
        
        surname_valid, surname_error = validate_name(surname, 'Фамилия')
        if not surname_valid:
            errors['surname'] = surname_error
        
        if errors:
            roles = Role.query.all()
            return render_template('user_form.html', 
                                 errors=errors, 
                                 form_data=request.form, 
                                 roles=roles,
                                 user=user,
                                 is_edit=True)
        
        try:
            user.surname = surname
            user.name = name
            user.patronymic = patronymic
            user.role_id = role_id if role_id else None
            db.session.commit()
            flash('Пользователь успешно обновлен', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при обновлении пользователя', 'error')
            roles = Role.query.all()
            return render_template('user_form.html', 
                                 errors={'general': 'Ошибка при обновлении пользователя'}, 
                                 form_data=request.form, 
                                 roles=roles,
                                 user=user,
                                 is_edit=True)
    
    roles = Role.query.all()
    return render_template('user_form.html', user=user, roles=roles, is_edit=True)

@app.route('/user/<int:user_id>/delete', methods=['POST'])
@check_rights(['delete_users'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при удалении пользователя', 'error')
    
    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        user = User.query.get(session['user_id'])
        errors = {}
        
        # Проверка старого пароля
        if not check_password_hash(user.password_hash, old_password):
            errors['old_password'] = "Неверный старый пароль"
        
        # Валидация нового пароля
        password_valid, password_error = validate_password(new_password)
        if not password_valid:
            errors['new_password'] = password_error
        
        # Проверка совпадения паролей
        if new_password != confirm_password:
            errors['confirm_password'] = "Пароли не совпадают"
        
        if errors:
            return render_template('change_password.html', errors=errors)
        
        try:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Пароль успешно изменен', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при изменении пароля', 'error')
    
    return render_template('change_password.html')

# Регистрация Blueprint будет выполнена после создания всех объектов

if __name__ == '__main__':
    # Регистрация Blueprint после создания всех объектов
    from reports import reports_bp
    app.register_blueprint(reports_bp)
    
    with app.app_context():
        db.create_all()
        
        # Создание ролей по умолчанию
        if not Role.query.first():
            admin_role = Role(name='Администратор', description='Полный доступ к системе')
            user_role = Role(name='Пользователь', description='Обычный пользователь')
            db.session.add(admin_role)
            db.session.add(user_role)
            db.session.commit()
            
            # Создание администратора по умолчанию
            admin_user = User(
                login='admin',
                password_hash=generate_password_hash('admin123'),
                name='Администратор',
                role_id=admin_role.id
            )
            db.session.add(admin_user)
            db.session.commit()
    
    app.run(debug=True)
