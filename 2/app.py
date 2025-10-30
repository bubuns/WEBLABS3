from flask import Flask, render_template, request, redirect, url_for, make_response
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route('/')
def index():
    """Главная страница с навигацией"""
    return render_template('index.html')

@app.route('/url_params')
def url_params():
    """Страница для отображения параметров URL"""
    params = request.args
    return render_template('url_params.html', params=params)

@app.route('/headers')
def headers():
    """Страница для отображения заголовков запроса"""
    headers = dict(request.headers)
    return render_template('headers.html', headers=headers)

@app.route('/cookies')
def cookies():
    """Страница для работы с cookies"""
    cookies = dict(request.cookies)
    return render_template('cookies.html', cookies=cookies)

@app.route('/set_cookie/<cookie_name>/<cookie_value>')
def set_cookie(cookie_name, cookie_value):
    """Установка cookie"""
    response = make_response(redirect(url_for('cookies')))
    response.set_cookie(cookie_name, cookie_value)
    return response

@app.route('/delete_cookie/<cookie_name>')
def delete_cookie(cookie_name):
    """Удаление cookie"""
    response = make_response(redirect(url_for('cookies')))
    response.set_cookie(cookie_name, '', expires=0)
    return response

@app.route('/form_params', methods=['GET', 'POST'])
def form_params():
    """Страница для отображения параметров формы"""
    if request.method == 'POST':
        form_data = request.form
        return render_template('form_params.html', form_data=form_data)
    return render_template('form_params.html')

@app.route('/phone_validation', methods=['GET', 'POST'])
def phone_validation():
    """Страница с формой для валидации номера телефона"""
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        error_message = None
        formatted_phone = None
        
        # Валидация номера телефона
        validation_result = validate_phone(phone)
        
        if validation_result['is_valid']:
            formatted_phone = validation_result['formatted']
        else:
            error_message = validation_result['error']
        
        return render_template('phone_validation.html', 
                             phone=phone, 
                             error_message=error_message, 
                             formatted_phone=formatted_phone)
    
    return render_template('phone_validation.html')

def validate_phone(phone):
    """Валидация и форматирование номера телефона"""
    if not phone:
        return {'is_valid': False, 'error': 'Недопустимый ввод. Неверное количество цифр.'}
    
    # Удаляем все символы кроме цифр и +
    digits_only = re.sub(r'[^\d+]', '', phone)
    
    # Проверяем на недопустимые символы
    allowed_chars = re.compile(r'^[\d\s\(\)\-\+\.]+$')
    if not allowed_chars.match(phone):
        return {'is_valid': False, 'error': 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'}
    
    # Извлекаем только цифры
    digits = re.sub(r'[^\d]', '', phone)
    
    # Проверяем длину
    if len(digits) == 11:
        if digits.startswith('7'):
            # +7 формат
            formatted = '8-' + digits[1:4] + '-' + digits[4:7] + '-' + digits[7:9] + '-' + digits[9:11]
            return {'is_valid': True, 'formatted': formatted}
        elif digits.startswith('8'):
            # 8 формат
            formatted = '8-' + digits[1:4] + '-' + digits[4:7] + '-' + digits[7:9] + '-' + digits[9:11]
            return {'is_valid': True, 'formatted': formatted}
        else:
            return {'is_valid': False, 'error': 'Недопустимый ввод. Неверное количество цифр.'}
    elif len(digits) == 10:
        # 10 цифр
        formatted = '8-' + digits[0:3] + '-' + digits[3:6] + '-' + digits[6:8] + '-' + digits[8:10]
        return {'is_valid': True, 'formatted': formatted}
    else:
        return {'is_valid': False, 'error': 'Недопустимый ввод. Неверное количество цифр.'}

if __name__ == '__main__':
    app.run(debug=True)
