from flask import Blueprint, render_template, request, jsonify, make_response
from app import db, User, VisitLog, check_rights
from datetime import datetime
import csv
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@check_rights(['view_own_visits'])
def index():
    """Главная страница журнала посещений"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Получаем записи с пагинацией
    visits = db.session.query(VisitLog, User).outerjoin(User, VisitLog.user_id == User.id)\
        .order_by(VisitLog.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('reports/index.html', visits=visits)

@reports_bp.route('/by_pages')
@check_rights(['view_own_visits'])
def by_pages():
    """Отчет по посещениям страниц"""
    # Получаем статистику по страницам
    stats = db.session.query(
        VisitLog.path,
        db.func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path)\
     .order_by(db.func.count(VisitLog.id).desc())\
     .all()
    
    return render_template('reports/by_pages.html', stats=stats)

@reports_bp.route('/by_users')
@check_rights(['view_own_visits'])
def by_users():
    """Отчет по посещениям пользователей"""
    # Получаем статистику по пользователям
    stats = db.session.query(
        User.surname,
        User.name,
        User.patronymic,
        db.func.count(VisitLog.id).label('count')
    ).outerjoin(VisitLog, User.id == VisitLog.user_id)\
     .group_by(User.id, User.surname, User.name, User.patronymic)\
     .order_by(db.func.count(VisitLog.id).desc())\
     .all()
    
    return render_template('reports/by_users.html', stats=stats)

@reports_bp.route('/by_pages/export')
@check_rights(['view_own_visits'])
def export_by_pages():
    """Экспорт отчета по страницам в CSV"""
    # Получаем статистику по страницам
    stats = db.session.query(
        VisitLog.path,
        db.func.count(VisitLog.id).label('count')
    ).group_by(VisitLog.path)\
     .order_by(db.func.count(VisitLog.id).desc())\
     .all()
    
    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Страница', 'Количество посещений'])
    
    for i, (path, count) in enumerate(stats, 1):
        writer.writerow([i, path, count])
    
    # Создаем ответ
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=visits_by_pages.csv'
    
    return response

@reports_bp.route('/by_users/export')
@check_rights(['view_own_visits'])
def export_by_users():
    """Экспорт отчета по пользователям в CSV"""
    # Получаем статистику по пользователям
    stats = db.session.query(
        User.surname,
        User.name,
        User.patronymic,
        db.func.count(VisitLog.id).label('count')
    ).outerjoin(VisitLog, User.id == VisitLog.user_id)\
     .group_by(User.id, User.surname, User.name, User.patronymic)\
     .order_by(db.func.count(VisitLog.id).desc())\
     .all()
    
    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['№', 'Пользователь', 'Количество посещений'])
    
    for i, (surname, name, patronymic, count) in enumerate(stats, 1):
        full_name = f"{surname or ''} {name} {patronymic or ''}".strip()
        if not full_name:
            full_name = "Неаутентифицированный пользователь"
        writer.writerow([i, full_name, count])
    
    # Создаем ответ
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=visits_by_users.csv'
    
    return response
