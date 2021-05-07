import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase

class UserToChallenge(SqlAlchemyBase):
    __tablename__ = 'user_to_challenge'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    challenge_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("challenges.id"))
    percent = sqlalchemy.Column(sqlalchemy.Integer)
    user = orm.relation('User')
    challenge = orm.relation('Challenge')

    def __repr__(self):
        return f'{self.user_id} {self.challenge_id} {self.percent}'