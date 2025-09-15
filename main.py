from flask import Flask,render_template,g,request,flash,redirect,url_for,make_response


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
app.config.from_object(__name__)


login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"

db.init_app(app)


from models import *


# def family_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         user = g.dbase.getUser(g.user)
#         if not user['family_id']:
#             flash("Вы ещё не состоите в семье", "warning")
#             return redirect(url_for('join_or_create_family'))
#         return f(*args, **kwargs)
#     return decorated_function

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html',nav=g.dbase.get_table('nav'),why_us = g.dbase.get_table('why_us'),steps =  g.dbase.get_table('steps'))

@app.route('/dashboard',methods= ['POST','GET'])
def dashboard():
    if request.method == 'POST':
        print(request.form)
        if not current_user.getFamilyId():
            flash('У вас нет семьи','error')
            return redirect(url_for('family'))
        for task_id in request.form.getlist('task_ids'):
            g.dbase.addTask(g.user,task_id,request.form.getlist(f'points_{task_id}')[0])
            try:
                u = UserTaskPoints(user_id =g.user, task_id = task_id, custom_points =request.form.getlist(f'points_{task_id}')[0])
                db.session.add(u)
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()
            flash('Задача добавлена','success')
    return render_template('dashboard.html',nav=g.dbase.get_table('nav'),tasks = g.dbase.getTasks(),user=g.dbase.getUser(g.user),family=g.dbase.getFamily(current_user.getFamilyId()),count_tasks = g.dbase.count_tasks_by_day(g.user),streak=g.dbase.get_current_streak(g.user))

@app.route('/login',methods=['POST','GET'])
def login():
    print(url_for('register'))
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    if request.method == 'POST':
        frm = request.form
        user = g.dbase.check_user(frm)
        if user:
            userlogin = UserLogin().create(user)
            rm = True if request.form.get('remember') else False
            login_user(userlogin, remember=rm)
            return redirect(url_for('profile'))
        else:
            flash('Неверный логин или пароль. Попробуйте ещё раз.','error')
    return render_template('login.html',nav=g.dbase.get_table('nav'))

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method == 'POST':
        user = request.form
        if not user['password'] == user['confirm_password']:
            flash("Неверный логин или пароль", "error")
            return redirect(url_for('register'))
        flash("Вы успешно зарегистрированы!", "success")
        g.dbase.add_user(user)
        try:

            u = Users(first_name=user['first_name'],last_name = user['last_name'],email=user['email'],password=user['password'],family = Families.query.all()[0] )
            db.session.add(u)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка добавления в БД {e}")
        return redirect(url_for('login'))
    return render_template('register.html',nav=g.dbase.get_table('nav'))


@app.route('/test')
def test():

    return str(UserTaskPoints.max_count_day(1,1))
@app.route('/profile')
@login_required
def profile():
    return render_template('profile2.html',nav=g.dbase.get_table('nav'),user=g.dbase.getUser(g.user),statistics = g.dbase.get_statistics(g.user),days_activity = g.dbase.get_week_activity(g.user),top_tasks = g.dbase.best_result(g.user),stats_summary=g.dbase.stats_summary(g.user),history=g.dbase.history_work(g.user),format_task_date = format_task_date)
@app.route('/userava')
@app.route('/userava/<int:user_id>')
def userava(user_id = None):
    if user_id:
        img = g.dbase.getAvatar(user_id)
    else:
        img = current_user.getAvatar()
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
    return render_template('edit_profile.html',nav=g.dbase.get_table('nav'),user=g.dbase.getUser(g.user))

@app.route('/family')
@login_required
def family():
    return render_template('family.html',nav=g.dbase.get_table('nav'),user=g.dbase.getUser(g.user),family=g.dbase.getFamily(current_user.getFamilyId()),lst_users=g.dbase.getFamilyUser((current_user.getFamilyId())),score=g.dbase.get_score,best_result_for_week = g.dbase.best_result_for_week,family_tasks = g.dbase.family_history_work(current_user.getFamilyId()),statistics=g.dbase.get_statistics_family(current_user.getFamilyId()),streak=g.dbase.get_current_streak)

@app.route('/join-family', methods=['GET', 'POST'])
@login_required
def join_family():
    if request.method == 'POST':
        g.dbase.addFamily(request.form['family_id'],g.user)
        return redirect(url_for('family'))
    return render_template('join_family.html', nav=g.dbase.get_table('nav'),user=g.dbase.getUser(g.user),families = g.dbase.getFamilies())

@app.route('/leave_family', methods = ['POST'])
@login_required
def leave_family():
    g.dbase.leave_family(g.user)
    return redirect(url_for('family'))

@app.route('/create_family',methods=['POST','GET'])
def create_family():
    if request.method == 'POST':
        if len(request.form['family_name'])>4:
            try:
                f = Families(name=request.form['family_name'])
                db.session.add(f)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
            g.dbase.createFamily(request.form['family_name'],g.user)
            return redirect(url_for('family'))
        else:
            flash("Некорректная длина имени семьи", "error")
    return render_template('create_family.html',nav=g.dbase.get_table('nav'),user=g.dbase.getUser(g.user))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта','success')
    return redirect(url_for('login'))

def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if not hasattr(g,'link_db'):
        g.link_db = connect_db()
    return g.link_db

@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, g.dbase)

@app.before_request
def zxc():
    n = get_db()
    g.dbase = FDataBase(n)
    g.user = current_user.get_id()


@app.teardown_request
def zxc(error):
    if hasattr(g,'link_db'):
        g.link_db.close()



def format_task_date(datetime_str):
    MONTHS_RU = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")  # или %Y-%m-%d %H:%M в зависимости от твоего формата
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