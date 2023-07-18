import json, sqlite3
import math
import os.path
import string
import time
import random

from flask import Flask, render_template, render_template_string, request, g, redirect, url_for, abort, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from flask_paginate import Pagination, get_page_parameter

from DatabaseProvider import DatabaseProvider
from UserLogin import UserLogin

from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'database.db'
SECRET_KEY = '*G-KaPdSgVkYp2s5'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'database.db')))

login_mgr = LoginManager(app)
login_mgr.login_view = 'login'


@login_mgr.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, DatabaseProvider(get()))


def connect():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row;
    return conn


def get():
    if not hasattr(g, 'link_db'):
        g.link_db = connect()
    return g.link_db


def create():
    db = connect()
    db.cursor().executescript(
        "CREATE TABLE IF NOT EXISTS users ("
        "uuid integer PRIMARY KEY AUTOINCREMENT,"
        "hwid text,"
        "register_time integer NOT NULL,"
        "email text NOT NULL,"
        "username text NOT NULL,"
        "password text NOT NULL,"
        "max_mem integer NOT NULL DEFAULT 2000,"
        "admin integer NOT NULL DEFAULT 0,"
        "buy_for integer NOT NULL"
        ");"
    )
    db.commit()
    db.close()


def templ(string: str):
    return render_template_string(string)


@app.route("/api/profile", methods=["POST"])
def user():
    db = get()
    provider = DatabaseProvider(db)
    user = getFromEmailOrUsername(request.form.get("username"), request.form.get("username"), provider)
    hwid = request.form.get("hwid")
    password = request.form.get("password")
    if hwid is None:
        return templ(json.dumps({"success": False, "message": "Хвид должен быть передан"})), 500

    if password is None:
        return templ(json.dumps({"success": False, "message": "Пароль должен быть передан"})), 500

    if user is None:
        return templ(json.dumps({"success": False, "message": f"Неверный логин или пароль"})), 404

    if not check_password_hash(user["password"], password):
        return templ(json.dumps({"success": False, "message": "Неверный логин или пароль"})), 500

    if int(round(time.time()*1000)) > user['buy_for']:
        return templ(json.dumps({"success": False, "message": "Длительность подписки истекла"})), 500

    jsonString = json.dumps({"success": True, "username": user['username'], "uuid": user["uuid"], "hwid":  provider.updateHWID(user["uuid"], hwid), "register_time": user["register_time"], "max-memory": user["max_mem"], "buy-for": user["buy_for"]})

    if hwid == json.loads(jsonString)['hwid']:
        return templ(jsonString), 200
    else:
        return templ(json.dumps({"success": False, "message": "Хвид не действителен"})), 500


@app.route("/api/profile/memory", methods=["POST"])
def memory():
    if not isinstance(current_user, UserLogin):
        return templ(json.dumps({"success": False, "message": "User not authorized"}))

    memory = request.form['memory']
    if memory is None or not memory.isdigit():
        return templ(json.dumps({"success": False, "message": "Memory arg requared and memory not str"}))

    db = get()
    provider = DatabaseProvider(db)

    mem = provider.updateMemory(current_user.get_id(), memory)
    return templ(json.dumps({"success": True, "message": f"Memory successfully set to {mem}", "memory": memory}))


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated: return redirect(url_for('profile', profile=current_user))

    if request.method == "GET":
        return render_template("login.html"), 200
    else:
        db = get()
        provider = DatabaseProvider(db)

        name = request.form['name']
        password = request.form['password']

        user = getFromEmailOrUsername(name, name, provider)

        if user is not None and check_password_hash(user['password'], password):
            userLogin = UserLogin().create(user)
            login_user(userLogin)
            return redirect(request.args.get("next") or url_for('profile', profile=current_user))
        else:
            return render_template("login.html", pull=True,
                                   pullMessage="Неверные данные"), 200


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        return render_template("register.html"), 200
    else:
        db = get()
        provider = DatabaseProvider(db)

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']

        if len(name) > 4 and len(email) > 4 and len(password) > 4 and len(password2) > 4 and password == password2:
            user = provider.getUserByUsername(name)
            email_user = provider.getUserByEmail(email)

            if user is not None:
                return render_template("register.html", pull=True, pullMessage="Аккаунт с таким именем уже зарегестрирован"), 200

            if email_user is not None:
                return render_template("register.html", pull=True,pullMessage="Аккаунт с такой почтой уже зарегестрирован"), 200

            hash = generate_password_hash(password)
            res = provider.createUser(email, name, hash)

            if res:
                return render_template("register.html", pull=True, pullMessage="Аккаунт успешно добавлен"), 200
            else:
                return render_template("register.html", pull=True, pullMessage=f"Ошибка во время добавления аккаунта, обратитесь к администрации {res}"), 200

        else:
            return render_template("register.html", pull=True, pullMessage="Проверьте правильность всех полей"), 200


def getFromEmailOrUsername(email: str, username: str, provider: DatabaseProvider):
    user = provider.getUserByUsername(username)
    email_user = provider.getUserByEmail(email)

    if user is not None:
        return user

    if email_user is not None:
        return email_user

    return None


@app.route("/admin/profile/update", methods=["POST"])
@login_required
def update():
    flag = current_user.user()['admin']
    if flag == 0:
        return abort(404)

    provider = DatabaseProvider(get())

    if request.form.get('uuid') is None:
        return templ(json.dumps({"success": False, "message": "ЮЮид должен быть передан"}))

    if request.form.get("memory") is not None:
        mem = provider.updateMemory(int(request.form.get("uuid")), int(request.form.get("memory")))
        return templ(json.dumps({"success": True, "message": f"Memory successfully set to {mem}"}))

    print(request.form)

    if request.form.get("buy_for") is not None:
        if request.form.get("buy_for") == "NaN":
            mem = provider.setBuyTime(int(request.form.get("uuid")), None)
        else:
            mem = provider.setBuyTime(int(request.form.get("uuid")), int(request.form.get("buy_for")))

        return templ(json.dumps({"success": True, "message": f"Buy time successfully set to {mem}"}))

    if request.form.get("hwid") is not None:
        if request.form.get("hwid") == "None":
            hwid = provider.setHWID(int(request.form.get("uuid")), None)
        else:
            hwid = provider.setHWID(int(request.form.get("uuid")), str(request.form.get("hwid")))

        return templ(json.dumps({"success": True, "message": f"HWID successfully set to {hwid}"}))

    return templ(json.dumps({"success": False, "message": "Нечего изменять"}))

@app.route("/admin/profile")
@login_required
def admin_profile():
    flag = current_user.user()['admin']
    if flag == 0:
        return abort(404)

    userid = request.args.get('uuid', 1, type=int)

    db = get()
    provider = DatabaseProvider(db)
    us = provider.getUserByUUID(userid)
    if us is None:
        return abort(404)

    return render_template("admin/userprofile.html", profile=current_user, user=us), 200


@app.route("/admin")
@login_required
def admin():
    flag = current_user.user()['admin']
    if flag == 0:
        return redirect(url_for('index'))

    db = get()
    provider = DatabaseProvider(db)

    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * 20  # вычислить смещение для среза списка пользователей

    db.cursor().execute(f"SELECT * FROM users ORDER BY `username` LIMIT 20 OFFSET {offset};")
    users_for_page = provider.getUsers(15, offset)

    return render_template("admin/admin.html", profile=current_user, users=users_for_page, current=page), 200


@login_required
@app.route("/download/loader")
def loader():
    if not isinstance(current_user, UserLogin):
        return abort(404)

    if current_user.user()['buy_for'] > int(round(time.time()*1000)) or current_user.user()['admin'] != 0:
        chars = string.digits
        return send_file("files/loader.exe", as_attachment=True,
                         download_name=''.join(random.choice(chars) for _ in range(8)) + ".exe")

    return abort(404)




@app.route("/")
def index():
    return render_template("index.html"), 200


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", profile=current_user), 200


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/elua")
def elua():
    return render_template("elua.html"), 200


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/error.html', code=404, message="Запрашиваемая страница не найдена"), 404


if __name__ == '__main__':
    create()
    app.run(debug=True, host="0.0.0.0", port=443)
