from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class WorkoutForm(FlaskForm):
    percent = StringField('Процент выполнения', validators=[DataRequired()])
    submit = SubmitField('Сохранить')