from functools import wraps
from check_rights import CheckRights
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask import Blueprint, render_template, redirect, send_file, url_for, request,flash
from app import db
from math import ceil

from auth import checkRole

import io

bp = Blueprint('logs', __name__, url_prefix='/logs')

PER_PAGE = 15

@bp.route("/visits")
@login_required
def show_user_logs():
    logs=None
    page = int(request.args.get('page',1))

    with db.connect().cursor(named_tuple=True) as cursor:
        if (current_user.can('prev_logs', current_user) == True):
            query = 'SELECT logs.*, users.first_name, users.second_name, users.middle_name FROM logs LEFT JOIN users ON logs.user_id = users.id ORDER BY created_at DESC LIMIT %s OFFSET %s '
            cursor.execute(query, (PER_PAGE, (page - 1) * PER_PAGE))
        else:
            query = f'SELECT logs.*, users.first_name, users.second_name, users.middle_name FROM logs LEFT JOIN users ON logs.user_id = users.id WHERE user_id = {int(current_user.id)} ORDER BY created_at DESC LIMIT %s OFFSET %s'
            cursor.execute(query, (PER_PAGE, (page - 1) * PER_PAGE))
        logs = cursor.fetchall()

    processed_logs = []
    for log in logs:
        if log.user_id == None:
            processed_logs.append(log._replace(user_id="Неаутентифицированный пользователь"))
        else:
            fio = f"{log.second_name} {log.first_name} {log.middle_name}"
            processed_logs.append(log._replace(user_id=fio))

    with db.connect().cursor(named_tuple=True) as cursor:
        if (current_user.can('prev_logs', current_user) == True):
            query = 'SELECT count(*) as count FROM logs'
            cursor.execute(query)
        else:
            query = f'SELECT count(*) as count FROM logs WHERE user_id = {int(current_user.id)}'
            cursor.execute(query)
        count = cursor.fetchone().count

    return render_template("log/visits.html", logs=processed_logs, count=ceil(count/PER_PAGE), page=page)

@bp.route("/users")
@checkRole('prev_logs')
@login_required
def show_count_logs():
    logs=None
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT user_id, users.first_name, users.second_name, users.middle_name, count(*) as count FROM logs LEFT JOIN users ON logs.user_id = users.id  group by user_id ORDER BY count DESC')
        cursor.execute(query)
        logs=cursor.fetchall()

    processed_logs = []
    for log in logs:
        if log.user_id == None:
            processed_logs.append(log._replace(user_id="Неаутентифицированный пользователь"))
        else:
            fio = f"{log.second_name} {log.first_name} {log.middle_name}"
            processed_logs.append(log._replace(user_id=fio))

    return render_template("log/users.html", logs=processed_logs)
@bp.route("/page")
@checkRole('prev_logs')
@login_required
def show_page_logs():
    logs=None
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT path,count(*) as count FROM logs group by path ORDER BY count DESC')
        cursor.execute(query)
        logs=cursor.fetchall()
    return render_template("log/page.html", logs=logs)

@bp.route("/export_csv_visits")
@login_required
def export_csv_visits():
    with db.connect().cursor(named_tuple=True) as cursor:
        if (current_user.can('prev_logs', current_user) == True):
            query = ('SELECT logs.*, users.first_name, users.second_name, users.middle_name FROM logs LEFT JOIN users ON logs.user_id = users.id ORDER BY created_at DESC')
            cursor.execute(query)
            logs = cursor.fetchall()
        else:
            query = (f'SELECT logs.*, users.first_name, users.second_name, users.middle_name FROM logs LEFT JOIN users ON logs.user_id = users.id WHERE user_id = {int(current_user.id)} ORDER BY created_at DESC')
            cursor.execute(query)
            logs = cursor.fetchall()

    processed_logs = []
    for log in logs:
        if log.user_id == None:
            processed_logs.append(log._replace(user_id="Неаутентифицированный пользователь"))
        else:
            fio = f"{log.second_name} {log.first_name} {log.middle_name}"
            processed_logs.append(log._replace(user_id=fio))

    data = load_data(processed_logs, ['user_id', 'path', 'created_at'])

    return send_file(data, as_attachment=True, download_name='download.csv')


@bp.route("/export_csv_users")
@login_required
def export_csv_users():
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT user_id, users.first_name, users.second_name, users.middle_name, count(*) as count FROM logs LEFT JOIN users ON logs.user_id = users.id  group by user_id ORDER BY count DESC')
        cursor.execute(query)
        logs = cursor.fetchall()

    processed_logs = []
    for log in logs:
        if log.user_id == None:
            processed_logs.append(log._replace(user_id="Неаутентифицированный пользователь"))
        else:
            fio = f"{log.second_name} {log.first_name} {log.middle_name}"
            processed_logs.append(log._replace(user_id=fio))

    data = load_data(processed_logs, ['user_id', 'count'])
    return send_file(data, as_attachment=True, download_name='download.csv')

@bp.route("/export_csv_page")
@login_required
def export_csv_page():
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT path, COUNT(*) as count FROM logs GROUP BY path ORDER BY count DESC')
        cursor.execute(query)
        logs = cursor.fetchall()
    data = load_data(logs, ['path', 'count'])
    return send_file(data, as_attachment=True, download_name='download.csv')

def load_data(records, fields):
    csv_data=", ".join(fields)+"\n"
    for record in records:
        csv_data += ", ".join([str(getattr(record, field, '')) for field in fields]) + "\n"
    f = io.BytesIO()
    f.write(csv_data.encode('utf-8'))
    f.seek(0)
    return f