from flask import Flask,render_template,g,request,flash,redirect,url_for,make_response
from werkzeug.security import generate_password_hash,check_password_hash

import sqlite3
from FDataBase import FDataBase
from flask_login import LoginManager,login_user,login_required,current_user,logout_user
from UserLogin import UserLogin
from functools import wraps
from datetime import datetime
from extensions import db


SECRET_KEY = 'sdifhisdhfiuehui989302uoisdjfjdru20'
DATABASE = 'instance/basedata.db'
MAX_CONTENT_LENGTH = 1024 * 1024

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['DEFAULT_AVATAR'] = 'static/images/default.jpg'
app.config.from_object(__name__)


login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"

db.init_app(app)


from models import *


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html',
                            nav=g.nav,
                            why_us = Why_us.query.all(),
                            steps = Steps.query.all())

@app.route('/dashboard',methods= ['POST','GET'])
def dashboard():
    if request.method == 'POST':
        if not current_user.getFamilyId():
            return redirect(url_for('family'))
        try:
            for task_id in request.form.getlist('task_ids'):
                u = UserTaskPoints(
                    user_id=current_user.get_id(),
                    task_id=task_id,
                    custom_points=request.form.get(f'points_{task_id}')
                )
                db.session.add(u)
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
    return render_template('dashboard.html',
                               nav=g.nav,
                               tasks = Tasks.query.all(),
                               user=g.user,
                               family=current_user.getFamilyId(),
                               count_tasks = UserTaskPoints.get_task_count(g.user_id,'today'),
                               streak=UserTaskPoints.get_user_activity(g.user_id))

@app.route('/login',methods=['POST','GET'])
def login():
    print(url_for('register'))
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    if request.method == 'POST':
        frm = request.form
        user = Users.query.filter(Users.email == frm['email']).first()
        print(user)
        if user:
            userlogin = UserLogin().fromDB(user)
            rm = True if request.form.get('remember') else False
            login_user(userlogin, remember=rm)
            return redirect(url_for('profile'))
        else:
            flash('Неверный логин или пароль. Попробуйте ещё раз.','error')
    return render_template('login.html',
                            nav=g.nav)

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method == 'POST':
        user = request.form
        if not user['password'] == user['confirm_password']:
            flash("Неверный логин или пароль", "error")
            return redirect(url_for('register'))
        try:
            password = generate_password_hash(user['password'])
            u = Users(first_name=user['first_name'],last_name = user['last_name'],email=user['email'],password=password)
            db.session.add(u)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка добавления в БД {e}")
        flash("Вы успешно зарегистрированы!", "success")
        return redirect(url_for('login'))
    return render_template('register.html',
                           nav=g.nav)


@app.route('/test')
def test():
    user = db.session.get(Users,current_user.get_id())
    if user:
        user.family_id = 2
        db.session.commit()
    return str('Привет')
@app.route('/profile')
@login_required
def profile():
    statistics = UserTaskPoints.get_scores(g.user_id)
    days_activity = UserTaskPoints.get_user_activity(g.user_id,'weekly')
    top_task = UserTaskPoints.get_most_completed_tasks(g.user_id)
    history = UserTaskPoints.get_last_tasks(g.user_id)
    stats_summary = {'total_tasks': UserTaskPoints.get_task_count(g.user_id),
                     'max_tasks_day': UserTaskPoints.max_count_day(g.user_id),
                     'active_days': UserTaskPoints.get_user_activity(g.user_id,mode='days_total')}

    return render_template('profile2.html',
                           nav=g.nav,
                           user=g.user,
                           statistics = statistics,
                           days_activity =days_activity ,
                           top_tasks = top_task,
                           stats_summary=stats_summary,
                           history=history,
                           format_task_date = format_task_date)
@app.route('/userava')
@app.route('/userava/<int:user_id>')
def userava(user_id = None):
    if user_id:
        usr = Users.query.filter(Users.id == user_id).scalar()
    else:
        usr = current_user.get_user()
    if not usr.avatar:
        try:
            with open(app.config['DEFAULT_AVATAR'], 'rb') as f:
                img = f.read()
        except FileNotFoundError as e:
            print('Не найдет автор по умолчанию')
    else:
        img = usr.avatar
    h = make_response(img)
    h.headers['Content_Type'] = 'image/png'
    return h
@app.route('/edit_profile',methods=['POST','GET'])
@login_required
def edit_profile():
    if request.method == "POST":
        id = g.user
        if request.files['photo']:
            img = request.files['photo'].read()
            g.dbase.updateUserAvatar(img, id)

        g.dbase.updateUserName(request.form['first_name'],request.form['last_name'],id)
        if request.form['password']:
            if request.form['password'] == request.form['confirm_password']:
                g.dbase.updateUserPasword(request.form['password'],id)
        return redirect(url_for('profile'))
    return render_template('edit_profile.html',
                           nav=g.nav,
                           user=g.user)

@app.route('/family')
@login_required
def family():
    return render_template('family.html',nav=g.nav,
                           user=g.user,
                           family=db.session.get(Families,current_user.getFamilyId()),
                           lst_users=Users.query.filter(Users.family_id == current_user.getFamilyId()).all(),
                           score=UserTaskPoints.get_scores,
                           best_result_for_week = UserTaskPoints.get_most_completed_tasks,
                           family_tasks = UserTaskPoints.get_last_tasks(current_user.getFamilyId(),scope='family'),
                           statistics=UserTaskPoints.get_scores(current_user.getFamilyId(),scope='family'),
                           streak=UserTaskPoints.get_user_activity,
                           format_task_date = format_task_date)

@app.route('/join-family', methods=['GET', 'POST'])
@login_required
def join_family():
    if request.method == 'POST':
        user = db.session.get(Users,current_user.get_id())
        if user:
            user.family_id = request.form['family_id']
            db.session.commit()
        return redirect(url_for('family'))
    families = Families.query.all()
    return render_template('join_family.html',
                           nav=g.nav,
                           user=g.user ,
                           families = families)

@app.route('/leave_family', methods = ['POST'])
@login_required
def leave_family():
    UserTaskPoints.query.filter(UserTaskPoints.user_id == current_user.get_id()).delete()
    family_id = current_user.getFamilyId()
    current_user.get_user().family_id = None
    if not Users.query.filter(Users.family_id == family_id).first():
        Families.query.filter(Families.id == family_id).delete()
    db.session.commit()
    return redirect(url_for('family'))

@app.route('/create_family',methods=['POST','GET'])
def create_family():
    if request.method == 'POST':
        if len(request.form['family_name'])>4:
            try:
                f = Families(name=request.form['family_name'])
                db.session.add(f)
                db.session.flush()
                user = db.session.get(Users, current_user.get_id())
                if user:
                    user.family_id = f.id
                db.session.commit()
            except Exception as e:
                db.session.rollback()
            return redirect(url_for('family'))
        else:
            flash("Некорректная длина имени семьи", "error")
    return render_template('create_family.html',
                           nav=g.nav,
                           user=g.user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта','success')
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(Users,int(user_id))
    if user:
        return UserLogin().fromDB(user)
    return None
@app.before_request
def load_globals():
    if current_user.is_authenticated:
        g.user = current_user.get_user()
        g.user_id = current_user.get_id()
    else:
        g.user = None
        g.user_id = None
    g.nav = Navigation.query.all()



def format_task_date(datetime_str):
    MONTHS_RU = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    dt = datetime.strptime(str(datetime_str), "%Y-%m-%d %H:%M:%S.%f")
    now = datetime.now()
    day = dt.day
    month = MONTHS_RU[dt.month]
    time_str = dt.strftime("%H:%M")

    if dt.year == now.year:
        return f"{day} {month} в {time_str}"
    else:
        return f"{day} {month} {dt.year} в {time_str}"


if __name__ == '__main__':
    app.run(debug=True)