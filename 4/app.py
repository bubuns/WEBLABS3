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

# Маршруты
@app.route('/')
def index():
    users = User.query.all()
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
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('view_user.html', user=user)

@app.route('/user/create', methods=['GET', 'POST'])
@login_required
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
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        surname = request.form['surname']
        name = request.form['name']
        patronymic = request.form['patronymic']
        role_id = request.form.get('role_id')
        
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
@login_required
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

if __name__ == '__main__':
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
