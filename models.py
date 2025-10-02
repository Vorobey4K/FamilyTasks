from main import db
from datetime import  datetime,date, timedelta
from sqlalchemy import func
from werkzeug.security import generate_password_hash,check_password_hash

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column( db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    avatar = db.Column(db.LargeBinary, nullable=True)

    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=True)
    family = db.relationship("Families", backref = db.backref('users', lazy='select'))

    cups = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<users:{self.first_name}>'


    def check_user(self,email,password):
        user = db.session.query(Users.password) \
            .filter(Users.email == email) \
            .scalar()
        print(user)
        print(password)
        if check_password_hash(user,password) and user:
            return user
        return False

class Families(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20),nullable = False)




class Tasks(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    default_points = db.Column(db.Integer,default=10)
    icon = db.Column(db.String(5))



class UserTaskPoints(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    custom_points = db.Column(db.Integer,nullable=True)

    task = db.relationship("Tasks", backref = db.backref('userstaskpoints', lazy='select'))

    @classmethod
    def period_filters(cls, periods=None):
        """Возвращает словарь фильтров по completed_at"""
        today = date.today()
        filters = {
            "today": lambda q: q.filter(func.date(cls.completed_at) == today),
            "week": lambda q: q.filter(cls.completed_at >= today - timedelta(days=7)),
            "month": lambda q: q.filter(cls.completed_at >= today.replace(day=1)),
        }
        if periods is None:
            return filters
        return {key: filters[key] for key in periods if key in filters}


    @classmethod
    def get_scores(cls, target_id, scope='user',periods=None):
        """Возвращает баллы пользователя или семьи за разные периоды"""
        if scope == "user":
            target_field = cls.user_id
        else:
            target_field = Users.family_id

        filters = cls.period_filters(periods)
        result = {}

        all_time_query = db.session.query(func.sum(cls.custom_points)) \
            .join(Users) \
            .filter(target_field == target_id)

        for key, filter_func in filters.items():
            result[key] = filter_func(all_time_query).scalar() or 0

        result['all_time'] = all_time_query.scalar() or 0
        print(result)
        return result


    @classmethod
    def get_most_completed_tasks(cls, user_id, period='all_time'):
        query = db.session.query(
            Tasks.name,
            func.count(cls.id).label("quantity")
        ).join(Tasks, cls.task_id == Tasks.id).filter(cls.user_id == user_id)

        if period != 'all_time':
            query = cls.period_filters(['week'])['week'](query)

        return query.group_by(Tasks.name) \
            .order_by(func.count(cls.id).desc()) \
            .limit(3) \
            .all()


    @classmethod
    def get_last_tasks(cls, target_id, scope='user'):
        if scope == 'user':
            target_field = cls.user_id
        else:
            target_field = Users.family_id

        query = db.session.query(
            Users.first_name,
            Tasks,
            cls.custom_points,
            cls.completed_at.label('date')
        ).join(Users, Users.id == cls.user_id) \
            .join(Tasks, Tasks.id == cls.task_id) \
            .filter(target_field == target_id) \
            .order_by(cls.completed_at.desc()) \
            .limit(20)

        return query.all()


    @classmethod
    def get_user_activity(cls, user_id, mode='streak'):
        dates = db.session.query(func.date(cls.completed_at)) \
            .filter(cls.user_id == user_id) \
            .group_by(func.date(cls.completed_at)) \
            .order_by(func.date(cls.completed_at).desc()) \
            .all()

        dates = [datetime.strptime(d[0], "%Y-%m-%d").date() for d in dates]
        today = date.today()

        if mode == 'days_total':
            return len(dates)

        if not dates and mode == 'streak':
            return [0]

        if mode == 'streak':
            streak = 0
            freeze = False
            flag = dates[0] if dates else None

            if dates[0] == today:
                streak = 1
            elif dates[0] == today - timedelta(days=1):
                streak = 1
                freeze = True
            else:
                return 0

            for dt in dates[1:]:
                if flag - dt == timedelta(days=1):
                    streak += 1
                    flag = dt
                else:
                    break
            return streak, freeze

        elif mode == 'weekly':
            dct_week = {0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'}
            activity = []
            days_week = []
            for i in range(7):
                activity.append(today in dates)
                days_week.append(today.weekday())
                today -= timedelta(days=1)
            days_week = list(map(lambda x: dct_week[x], days_week))
            return days_week[::-1], activity[::-1]


    @classmethod
    def get_task_count(cls, user_id, period='all_time'):
        query = db.session.query(func.count(cls.id)).filter(cls.user_id == user_id)
        if period == 'today':
            query = query.filter(func.date(cls.completed_at) == date.today())
        return query.scalar() or 0


    @classmethod
    def max_count_day(cls, user_id):
        subq = db.session.query(func.count(cls.id).label('cnt')) \
            .filter(cls.user_id == user_id) \
            .group_by(func.date(cls.completed_at)) \
            .subquery()
        return db.session.query(func.max(subq.c.cnt)).scalar() or 0






class Navigation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    url = db.Column(db.String(30), nullable=False)



class Steps(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(50), nullable=False)



class Why_us(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(5))
    description = db.Column(db.String(50), nullable=False)