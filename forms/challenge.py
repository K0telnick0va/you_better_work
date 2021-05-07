from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class ChallengeForm(FlaskForm):
    text = StringField('Текст', validators=[DataRequired()])
    ref = StringField('Ссылка на YouTube', validators=[DataRequired()])
    submit = SubmitField('Применить')