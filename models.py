from main import db
from datetime import  datetime,date, timedelta
from sqlalchemy import func
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
        """Возвращает словарь фильтров для статистики по completed_at"""
        today = date.today()
        filters = {
            "today": lambda q: q.filter(func.date(cls.completed_at) == today),
            "week": lambda q: q.filter(cls.completed_at >= today - timedelta(days=7)),
            "month": lambda q: q.filter(cls.completed_at >= today.replace(day=1)),
        }

        if periods is None:  # вернуть все
            return filters

        # вернуть только нужные
        return {key: filters[key] for key in periods if key in filters}

    def get_scores(self, target_id, scope='user'):
        """Возвращает баллы пользователя или семьи за день, неделю, месяц и всё время"""
        target_id = target_id
        if scope == "user":
            target_field = UserTaskPoints.user_id
        else:
            target_field = Users.family_id

        today = date.today()

        filters = UserTaskPoints.period_filters()

        result = {}

        all_time = db.session.query(func.sum(UserTaskPoints.custom_points)) \
            .join(Users) \
            .filter(target_field == target_id)

        for key,value in filters.items():
            result[key] = value(all_time).scalar() or 0

        result['all_time'] = all_time.scalar() or 0
        return result

    def get_most_completed_tasks(self,user_id,period ='all_time'):
        """Возвращает имена самых популярных задач за неделю или за все время"""
        query  = db.session.query(Tasks.name,func.count(UserTaskPoints.id).label("quantity")) \
            .join(Tasks, UserTaskPoints.task_id == Tasks.id) \
            .filter(UserTaskPoints.user_id == user_id)

        if not period == 'all_time':
            filters = UserTaskPoints.period_filters(['week'])
            query  = filters['week'](query )

        query = query.group_by(Tasks.name) \
            .order_by(func.count(UserTaskPoints.id).desc()) \
            .limit(3)

        return query.all()


    def get_last_tasks(self,target_id,scope='user'):
        print(target_id)
        """Возвращает  последние задачи с полными данными для пользователя или семьи"""

        target_id = target_id
        if scope == "user":
            target_field = UserTaskPoints.user_id
        else:
            target_field = Users.family_id

        query = db.session.query(Users.first_name,Tasks,UserTaskPoints.custom_points,UserTaskPoints.completed_at) \
            .select_from(UserTaskPoints) \
            .join(Users, Users.id == UserTaskPoints.user_id) \
            .join(Tasks, Tasks.id == UserTaskPoints.task_id) \
            .filter(target_field == target_id) \
            .order_by(UserTaskPoints.completed_at.desc()) \
            .limit(20)

        return query.all()

    def get_user_activity(self,user_id,mode='streak'):
        """
        Возвращает статистику активности пользователя.

        :param user_id: ID пользователя
        :param mode: режим подсчёта:
            - "streak" → текущий стрик (подряд дни до сегодня)
            - "weekly" → активность по каждому дню недели
            - "days_total" → общее количество активных дней (не подряд)
        :return: число или словарь с данными (зависит от режима)
        """
        dates = db.session.query(func.date(UserTaskPoints.completed_at)) \
            .filter(UserTaskPoints.user_id == user_id) \
            .group_by(func.date(UserTaskPoints.completed_at)) \
            .order_by(UserTaskPoints.completed_at.desc()) \
            .all()
        print(dates)

        if mode == 'days_total':
            return len(dates)

        dates = [datetime.strptime(d[0], "%Y-%m-%d").date() for d in dates]
        today = date.today()

        if not dates and mode =='streak':
            return 0

        if mode == "streak":
            streak = 0
            freeze = False

            if dates[0] == today:
                streak = 1
                flag = today
            elif dates[0] == today - timedelta(days=1):
                streak = 1
                flag = today - timedelta(days=1)
                freeze = True
            else:
                return 0

            for dt in dates[1:]:
                if flag - dt == timedelta(days=1):
                    streak += 1
                    flag = dt
                else:
                    break
            return streak,freeze

        elif mode == "weekly":
            result = []
            for day in range(7):
                if today in dates:
                    result.append(True)
                else:
                    result.append(False)
                today = today -timedelta(days=1)

            return result[::-1]


    def get_task_count(self,user_id,period='all_time'):
        query = db.session.query(func.count(UserTaskPoints.id)) \
            .filter(UserTaskPoints.user_id == user_id)
        print(query.all())
        if period == 'today':
            query = query.filter(func.date(UserTaskPoints.completed_at) == date.today())
        return query.scalar() or 0


    def max_count_day(self,user_id):
        query = db.session.query(func.count(UserTaskPoints.id).label('cnt')) \
            .filter(UserTaskPoints.user_id == user_id) \
            .group_by(func.date(UserTaskPoints.completed_at)) \
            .subquery()
        query= db.session.query(func.max(query.c.cnt))
        return query.scalar() or 0






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