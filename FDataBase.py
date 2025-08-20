import sqlite3
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import date, timedelta,datetime

class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()


    def get_table(self,n_table):
        try:
            self.__cur.execute(f'SELECT * FROM {n_table}')
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print(f'Ошибка {e}')
        return False


    def add_user(self,form):
        first_name = form['first_name']
        last_name = form['last_name']
        email = form['email']
        password = generate_password_hash(form['password'])
        self.__cur.execute('INSERT INTO users (first_name,last_name,email,password) VALUES (?,?,?,?)',(first_name,last_name,email,password))
        self.__db.commit()


    def check_user(self,form):
        self.__cur.execute('SELECT * FROM users WHERE email LIKE ?',(form['email'],))
        res = self.__cur.fetchone()
        if res:
            if check_password_hash(res['password'],form['password']):
                return res
        return False




    def getUser(self,id):
        self.__cur.execute('SELECT * FROM users WHERE id = ?',(id,))
        res = self.__cur.fetchone()
        return res


    def edit_profile(self,form,files,id):
        prof = self.getUser(id)
        f_name = prof['first_name']
        l_name = prof['last_name']
        password = prof['password']
        #if form['first_name'] !=

    def updateUserAvatar(self,img,id):
        binary = sqlite3.Binary(img)
        self.__cur.execute('UPDATE users SET avatar = ? WHERE id = ?',(binary,id))
        self.__db.commit()

    def updateUserName(self,first,last,id):
        self.__cur.execute('UPDATE users SET first_name = ? WHERE id = ?', (first, id))
        self.__cur.execute('UPDATE users SET last_name = ? WHERE id = ?', (last, id))
        self.__db.commit()

    def updateUserPasword(self,password,id):
        password = generate_password_hash(password)
        self.__cur.execute('UPDATE users SET password = ? WHERE id = ?', (password, id))
        self.__db.commit()


    def createFamily(self,name,id):
        self.__cur.execute('INSERT INTO families (name,creator_id) VALUES(?,?)',(name,id))
        self.__cur.execute('SELECT id FROM families WHERE name = ?',(name,))
        res = self.__cur.fetchone()
        self.__cur.execute('UPDATE users SET family_id = ? WHERE id = ?',(res['id'],id))
        self.__db.commit()

    def getFamily(self,family_id):
        self.__cur.execute('SELECT * FROM families WHERE id = ?',(family_id,))
        res = self.__cur.fetchone()
        return res


    def getFamilies(self):
        self.__cur.execute('''SELECT families.id, name, count(*) as len from families
                                JOIN users ON families.id = users.family_id
                                GROUP BY families.id''')
        return self.__cur.fetchall()

    def addFamily(self,id_family,id_user):
        self.__cur.execute('UPDATE users SET family_id = ? WHERE id = ?', (id_family, id_user))
        self.__db.commit()


    def getAvatar(self,id):
        img = None
        self.__cur.execute('SELECT * FROM users WHERE id = ?',(id,))
        user = self.__cur.fetchone()
        if not user['avatar']:
            try:
                with open('static/images/default.jpg', 'rb') as f:
                    img = f.read()
            except FileNotFoundError as e:
                print('Не найдет автор по умолчанию')
        else:
            img = user['avatar']
        return img

    def getTasks(self):
        self.__cur.execute('SELECT * FROM tasks')
        return self.__cur.fetchall()


    def addTask(self,user_id,task_id,score):
        print(user_id,task_id,score)
        self.__cur.execute('INSERT INTO user_task_points (user_id,task_id,custom_points) VALUES (?,?,?)',(user_id,task_id,score))
        self.__db.commit()


    def getFamilyUser(self,family_id):
        self.__cur.execute('SELECT * FROM users WHERE family_id = ?',(family_id,))
        res = self.__cur.fetchall()
        return sorted(res,key = lambda x: self.get_score(x['id']),reverse=True)



    def get_score(self,id):
        week =  date.today() - timedelta(days=7)
        self.__cur.execute('''SELECT sum(user_task_points.custom_points) AS total_points
                                FROM user_task_points
                                JOIN tasks ON user_task_points.task_id = tasks.id
                                WHERE user_task_points.user_id = ? AND DATE(completed_at) >= ?;''',(id,week))
        return self.__cur.fetchone()[0] or 0


    def get_statistics(self,user_id):
        dct = {}
        today = date.today()
        dct['start_week'] = today - timedelta(days=7)
        dct['start_month'] = today.replace(day=1)
        self.__cur.execute('''SELECT SUM(user_task_points.custom_points) AS total_points
                                FROM user_task_points
                                WHERE user_task_points.user_id = ? AND DATE(completed_at) = ?;''',(user_id,today))
        result = {}
        result['today'] = self.__cur.fetchone()[0] or 0
        for name,time in dct.items():
            self.__cur.execute('''SELECT SUM(user_task_points.custom_points) AS total_points
                                FROM user_task_points
                                WHERE user_task_points.user_id = ? AND DATE(completed_at) >= ?;''',(user_id,time))

            result[name] = self.__cur.fetchone()[0] or 0
        self.__cur.execute('''SELECT SUM(user_task_points.custom_points) AS total_points
                                FROM user_task_points
                                WHERE user_task_points.user_id = ? ''',(user_id,))
        result['all_time'] = self.__cur.fetchone()[0] or 0
        return result

    def get_statistics_family(self,family_id):
        dct = {}
        today = date.today()
        dct['start_week'] = today - timedelta(days=7)
        dct['start_month'] = today.replace(day=1)
        self.__cur.execute('''SELECT SUM(user_task_points.custom_points) AS total_points
                                FROM user_task_points
                                JOIN users ON users.id = user_task_points.user_id
								WHERE family_id = ? AND DATE(completed_at) = ?''',
                           (family_id, today))
        result = {}
        result['today'] = self.__cur.fetchone()[0] or 0
        for name,time in dct.items():
            self.__cur.execute('''SELECT SUM(user_task_points.custom_points) AS total_points
                                FROM user_task_points
                                JOIN users ON users.id = user_task_points.user_id
                                WHERE family_id = ? AND DATE(completed_at) >= ?;''',(family_id,time))
            result[name] = self.__cur.fetchone()[0] or 0
        self.__cur.execute('''SELECT SUM(user_task_points.custom_points) AS total_points
                                FROM user_task_points
                                JOIN users ON users.id = user_task_points.user_id
                                WHERE family_id = ? ''',(family_id,))
        result['all_time'] = self.__cur.fetchone()[0] or 0
        return result
    def best_result_for_week(self,id):

        week = date.today() - timedelta(days=7)
        print(week)
        self.__cur.execute('''SELECT tasks.name,COUNT(*) as summa,tasks.icon FROM user_task_points
                                JOIN tasks ON tasks.id = user_task_points.task_id
                                WHERE user_task_points.user_id = ? AND DATE(completed_at) >= ?
                                GROUP BY tasks.name
                                ORDER BY summa DESC
                                LIMIT 3''',(id,week))
        return self.__cur.fetchall()

    def best_result(self,id):
        self.__cur.execute('''SELECT tasks.name,COUNT(*) as summa,tasks.icon FROM user_task_points
                                        JOIN tasks ON tasks.id = user_task_points.task_id
                                        WHERE user_task_points.user_id = ?
                                        GROUP BY tasks.name
                                        ORDER BY summa DESC
                                        LIMIT 3''', (id,))
        return self.__cur.fetchall()
    def count_tasks_by_day(self,user_id):
        today = date.today()
        self.__cur.execute('''SELECT COUNT(*)
                                FROM user_task_points
                                WHERE user_task_points.user_id = ? AND DATE(completed_at) = ?;''',
                           (user_id, today))
        return self.__cur.fetchone()[0]


    def get_current_streak(self,user_id):
        self.__cur.execute('''SELECT DATE(completed_at) as zxc
                                FROM user_task_points
                                WHERE user_task_points.user_id = ? 
                                GROUP BY zxc
                                ORDER BY zxc DESC''',(user_id,))
        dates = self.__cur.fetchall()

        if not dates:
            print(dates)
            return 0,True
        if date.today() == datetime.strptime(dates[0][0],'%Y-%m-%d').date():
            streak = 1
            freeze = False
        elif date.today()-timedelta(days=1) == datetime.strptime(dates[0][0],'%Y-%m-%d').date():
            streak = 1
            freeze = True
        else:
            return 0,True
        flag = date.today()- timedelta(days=1) if freeze else date.today()
        for i in dates[1:]:
            date_obj = datetime.strptime(i[0],'%Y-%m-%d').date()
            if flag - date_obj == timedelta(days=1):
                streak += 1
                flag = date_obj
            else:
                break
        return streak,freeze


    def get_week_activity(self,user_id):
        dct_week = {0:'Пн',1:'Вт',2:'Ср',3:'Чт',4:'Пт',5:'Сб',6:'Вс'}
        day = date.today()
        days_week = []
        activity = []
        for _ in range(7):
            self.__cur.execute('''SELECT * FROM user_task_points 
                                WHERE user_id = ? and DATE(completed_at) = ?''',(user_id,day))
            activity.append(True if self.__cur.fetchone() else False)
            days_week.append(day.weekday())
            day -=timedelta(days=1)
        return list(map(lambda x:dct_week[x],days_week))[::-1],activity[::-1]


    def stats_summary(self,user_id):
        res = {}
        self.__cur.execute('SELECT COUNT(*) FROM user_task_points WHERE user_id = ?',(user_id,))
        res['total_tasks'] = self.__cur.fetchone()[0] or 0
        self.__cur.execute('''SELECT max(task_count) FROM (
                                SELECT count(*) as task_count 
                                FROM user_task_points
                                WHERE user_id = ?
                                GROUP by DATE(completed_at))''',(user_id,))
        res['max_tasks_day'] = self.__cur.fetchone()[0] or 0
        self.__cur.execute('''SELECT COUNT(*) FROM (
                                SELECT 1
                                FROM user_task_points
                                WHERE user_id = ?
                                GROUP BY DATE(completed_at)
                            )''',(user_id,))
        res['active_days'] = self.__cur.fetchone()[0] or 0
        return res

    def history_work(self,user_id):
        self.__cur.execute('''SELECT completed_at as date,tasks.name, custom_points as points,icon,default_points FROM user_task_points
                                JOIN tasks ON tasks.id = user_task_points.task_id
                                WHERE user_task_points.user_id = ?
                                ORDER BY completed_at DESC''',(user_id,))
        return self.__cur.fetchall()

    def family_history_work(self,family_id):
        self.__cur.execute('''SELECT users.first_name,users.last_name,tasks.name, custom_points as points,icon FROM user_task_points
                                JOIN tasks ON tasks.id = user_task_points.task_id
								JOIN users ON user_task_points.user_id = users.id
                                WHERE users.family_id = ?
                                ORDER BY completed_at DESC''',(family_id,))
        return self.__cur.fetchall()



    def leave_family(self,user_id):
        self.__cur.execute('''DELETE FROM user_task_points
                                    WHERE user_id = ?''',(user_id,))
        self.__cur.execute('''SELECT family_id FROM users
                                WHERE id = ?''',(user_id,))
        family_id = self.__cur.fetchone()[0]
        self.__cur.execute('''UPDATE users SET family_id = NULL
                                    WHERE id = ?''', (user_id,))
        self.__cur.execute('''SELECT * FROM users
                                WHERE family_id = ?''',(family_id,))
        if not self.__cur.fetchone():
            self.__cur.execute('''DELETE FROM families
                                    WHERE id = ?''',(family_id,))
        self.__db.commit()