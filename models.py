import os

from app import db
from sqlalchemy.dialects.postgresql import JSON


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(), primary_key=True)
    subjects = db.Column(JSON)
    assignments = db.Column(JSON)

    def __init__(self, id, subjects, assignments):
        self.id = id
        self.subjects = subjects
        self.assignments = assignments

    def __repr__(self):
        return '<id {}>'.format(self.id)
