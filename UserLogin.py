import time
from datetime import datetime

from flask_login import UserMixin


class UserLogin(UserMixin):
    def __init__(self):
        self.__user = None

    def fromDB(self, user_uuid, provider):
        self.__user = provider.getUserByUUID(user_uuid)
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user['uuid'])

    def user(self):
        return self.__user

    def getFormattedCreateTime(self):
        timestamp = self.__user['register_time']
        d = datetime.fromtimestamp(timestamp/1000)
        return d.strftime('%d.%m.%Y %H:%M')

    def getRank(self):
        if self.__user['admin'] == 1:
            return "Администратор"

        elif self.__user['admin'] == 0:
            return "Пользователь"

    def getHWID(self):
        if self.__user['hwid'] is None:
            return "Неизвестен"
        else:
            return self.__user['hwid']

    def canDownload(self) -> bool:
        return self.__user['buy_for'] > int(round(time.time()*1000)) or self.__user['admin'] == 1

    def buyFor(self):
        if self.__user['buy_for'] == 0:
            return "Не куплен"

        else:
            timestamp = self.__user['buy_for']
            d = datetime.fromtimestamp(timestamp/1000)
            return d.strftime('%d.%m.%Y %H:%M')