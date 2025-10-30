from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к запрашиваемой странице необходимо пройти процедуру аутентификации.'
login_manager.login_message_category = 'info'

# Простой класс пользователя
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Создаем тестового пользователя
users = {
    1: User(1, 'user', generate_password_hash('qwerty'))
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/counter')
def counter():
    # Увеличиваем счетчик посещений в сессии
    if 'visit_count' not in session:
        session['visit_count'] = 0
    session['visit_count'] += 1
    
    return render_template('counter.html', count=session['visit_count'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember') == 'on'
        
        # Ищем пользователя
        user = None
        for u in users.values():
            if u.username == username:
                user = u
                break
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash('Вы успешно вошли в систему!', 'success')
            
            # Перенаправляем на запрашиваемую страницу или на главную
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('index'))

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')

if __name__ == '__main__':
    app.run(debug=True)
