from flask_login import UserMixin
class UserLogin(UserMixin):
    def fromDB(self, user):
        self.__user = user
        return self

    def get_user(self):
        return self.__user


    def get_id(self):
        return str(self.__user.id)

    def getAvatar(self):
        img = None
        if not self.__user.avatar:
            try:
                with open('static/images/default.jpg','rb') as f:
                    img = f.read()
            except FileNotFoundError as e:
                print('Не найдет автор по умолчанию')
        else:
            img = self.__user.avatar
        return img


    def getFamilyId(self):
        res = self.__user.family_id
        return str(res) if res is not None else None



