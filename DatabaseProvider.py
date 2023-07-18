import math
import sqlite3
import time


class DatabaseProvider:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def getUsers(self, limit: int, offset: int) -> list:
        try:
            if limit is None:
                limit = 999999999999999
            if offset is None:
                offset = 0

            self.__cur.execute(f"SELECT * FROM users ORDER BY uuid LIMIT {limit} OFFSET {offset}")
            res = self.__cur.fetchall()
            if res: return res
        except:
            print("Error when read DB")

        return []

    def createUser(self, email: str, username: str, password: str) -> str:
        try:
            if self.getUserByUsername(username) is not None or self.getUserByEmail(email) is not None:
                return "error Никнейм или почта занята"

            t = int(round(time.time()*1000))
            self.__cur.execute("INSERT INTO users VALUES(NULL, NULL, ?, ?, ?, ?, ?, ?, ?)", (t, email, username, password, 2000, 0, 0))
            self.__db.commit()
            return "success"
        except sqlite3.Error as e:
            print("Error when add new user " + str(e))
            return f"error {e}"

    def getUserByUsername(self, username: str):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE username = '{username}'")
            res = self.__cur.fetchone()
            if res:
                return res
            else:
                return None

        except sqlite3.Error as e:
            print(str(e))
            return None

    def getUserByEmail(self, email: str):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email = '{email}'")
            res = self.__cur.fetchone()
            if res:
                return res
            else:
                return None
        except sqlite3.Error as e:
            print(str(e))
            return None

    def getUserByUUID(self, uuid: int):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE uuid = '{uuid}'")
            res = self.__cur.fetchone()
            if res:
                return res
            else:
                return None
        except sqlite3.Error as e:
            print(str(e))
            return None

    def updateMemory(self, uuid: int, memory: int):
        try:
            if self.getUserByUUID(uuid) is None:
                return False

            self.__cur.execute(f"UPDATE users SET max_mem='{memory}' WHERE uuid={uuid}")
            self.__db.commit()
            return self.getUserByUUID(uuid)["max_mem"]
        except Exception as e:
            print(str(e))
            return self.getUserByUUID(uuid)["max_mem"]

    def updateHWID(self, uuid: int, hwid: str) -> bool:
        try:
            if self.getUserByUUID(uuid) is None:
                return False

            self.__cur.execute(f"SELECT hwid FROM users WHERE uuid={uuid}")
            result = self.__cur.fetchone()
            if result[0] is None or result[0] == "None":
                self.__cur.execute(f"UPDATE users SET hwid='{hwid}' WHERE uuid={uuid}")
                self.__db.commit()
            return self.getUserByUUID(uuid)["hwid"]
        except Exception as e:
            print(str(e))
            return self.getUserByUUID(uuid)["hwid"]

    def setHWID(self, uuid: int, hwid) -> bool:
        try:
            if self.getUserByUUID(uuid) is None:
                return False

            if hwid is None:
                self.__cur.execute(f"UPDATE users SET hwid=NULL WHERE uuid={uuid}")
            else: self.__cur.execute(f"UPDATE users SET hwid='{hwid}' WHERE uuid={uuid}")

            self.__db.commit()
            return self.getUserByUUID(uuid)["hwid"]
        except Exception as e:
            print(str(e))
            return self.getUserByUUID(uuid)["hwid"]

    def setBuyTime(self, uuid: int, buy) -> bool:
        try:
            if self.getUserByUUID(uuid) is None:
                return False

            self.__cur.execute(f"UPDATE users SET buy_for={buy} WHERE uuid={uuid}")
            self.__db.commit()
            return self.getUserByUUID(uuid)["buy_for"]
        except Exception as e:
            print(str(e))
            return self.getUserByUUID(uuid)["buy_for"]
