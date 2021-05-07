from flask import Flask, render_template, redirect, session, make_response, abort, request
from data import db_session
from data.users import User
from data.challenges import Challenge
from data.user_to_challenge import UserToChallenge
from forms.user import RegisterForm
from forms.challenge import ChallengeForm
from forms.workout_form import WorkoutForm
from flask_login import login_user, logout_user, login_required, current_user
from forms.login_form import LoginForm
from flask_login import LoginManager
import requests
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(name=form.name.data,
            email=form.email.data, height=form.height.data, weight=form.weight.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    # получаем красивую случайную цитату, если повезёт - о спорте

    url = "https://andruxnet-random-famous-quotes.p.rapidapi.com/"

    querystring = {"cat": "famous", "count": "1"}

    headers = {
        'x-rapidapi-key': "0022036191msh585e72fabb6c3eap147cd5jsn7d472340fe13",
        'x-rapidapi-host': "andruxnet-random-famous-quotes.p.rapidapi.com"
    }

    response = requests.request("POST", url, headers=headers, params=querystring).json()

    quote = response[0]['quote']

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    fields = user.to_dict(only=('name', 'height', 'weight', 'uploaded_videos'))

    # считаем, сколько у пользователя было тренировок (через асс. таблицу)

    info = list(db_sess.query(UserToChallenge).filter(UserToChallenge.user_id == user.id).all())

    return render_template('profile.html', title='Мой профиль',
                           name=fields['name'], height=fields['height'],
                           weight=fields['weight'], uploaded_videos=fields['uploaded_videos'],
                           amount=len(info), quote=quote)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/week_challenges')
@login_required
def challenges():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        chngs = db_sess.query(Challenge)

    return render_template('week_challenges.html', challenges=chngs)

@app.route('/challenge',  methods=['GET', 'POST'])
@login_required
def add_challenge():
    form = ChallengeForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        challenge = Challenge()

        existing_days = db_sess.query(Challenge).all()
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        if len(list(existing_days)) == 7:
            day = days[0]
            for video in existing_days:
                db_sess.delete(video)  # начинаем новую неделю, старые видео удаляются
        else:
            day = days[len(list(existing_days))]

        challenge.day = day
        challenge.user_id = current_user.id
        challenge.text = form.text.data

        ref = form.ref.data.split('=')[1]
        challenge.video_id = ref

        db_sess.add((challenge))
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.uploaded_videos += 1
        db_sess.commit()
        return redirect('/week_challenges')
    return render_template('challenge.html', title='Добавление тренировки',
                           form=form)

@app.route('/challenge/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_challenge(id):
    form = ChallengeForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        challenge = db_sess.query(Challenge).filter(Challenge.id == id).first()
        if challenge:
            form.text.data = challenge.text
            form.ref.data = 'вы не можете заменить видео'
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        challenge = db_sess.query(Challenge).filter(Challenge.id == id).first()
        if challenge:
            challenge.text = form.text.data
            db_sess.commit()
            return redirect('/week_challenges')
        else:
            abort(404)
    return render_template('challenge.html',
                           title='Изменение тренировки',
                           form=form
                           )

@app.route('/delete_challenge/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_challenge(id):
    db_sess = db_session.create_session()
    challenge = db_sess.query(Challenge).filter(Challenge.id == id).first()
    if challenge:
        db_sess.delete(challenge)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/week_challenges')

@app.route('/workout/<int:challenge_id>/<int:user_id>', methods=['GET', 'POST'])
@login_required
def workout(challenge_id, user_id):
    form = WorkoutForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user_to_challenge = UserToChallenge()
        user_to_challenge.user_id = user_id
        user_to_challenge.challenge_id = challenge_id
        user_to_challenge.percent = form.percent.data
        db_sess.add(user_to_challenge)
        db_sess.commit()
        return redirect('/week_challenges')
    return render_template('workout.html', title='Тренировка', form=form)

@app.route('/stat', methods=['GET', 'POST'])
@login_required
def stat():
    db_sess = db_session.create_session()
    info = list(db_sess.query(UserToChallenge).all()) # выгружаем результаты по всем пользователям
    results = {}
    for row in info:
        record = [int(i) for i in str(row).split()]
        if record[0] not in results:
            results[record[0]] = [(record[1], record[2])]
        else:
            results[record[0]] += [(record[1], record[2])]

    max_count = -1 # чаще всех тренировался
    max_count_id = -1
    max_eff = -1 # самый лучший средний процент тренировок
    max_eff_id = -1
    for i in results.keys():
        if len(results[i]) > max_count:
            max_count_id = i
            max_count = len(results[i])
        percent = 0
        for day in results[i]:
            percent += day[1]
        eff = percent // len(results[i])
        if eff > max_eff:
            max_eff = eff
            max_eff_id = i

    print(max_count_id, max_eff_id)
    count_user = db_sess.query(User).filter(User.id == max_count_id).first()
    eff_user = db_sess.query(User).filter(User.id == max_eff_id).first()

    db_sess.commit()
    return render_template('stat.html', title='Статистика', count_user=count_user,
                           eff_user=eff_user, max_count=max_count, max_eff=max_eff)

if __name__ == '__main__':
    db_session.global_init("db/workouts.sqlite")
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)