import json
import os
from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app import db
from sqlalchemy.dialects.postgresql import JSON


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.String(), primary_key=True)
    modules = db.Column(JSON)
    telegram_id = db.Column(db.Integer())
    token = db.Column(db.String())
    notes = relationship("Notes")
    assignments = relationship("Assignments")

    def __init__(self, user_id, modules, telegram_id, token):
        self.user_id = user_id
        self.modules = modules
        self.telegram_id = telegram_id
        self.token = token

    def __repr__(self):
        return '<id {}>'.format(self.user_id)


class Notes(db.Model):
    __tablename__ = 'notes'

    note_id = db.Column(db.String(), primary_key=True)
    user_id = db.Column(db.String(), ForeignKey('users.user_id'))
    module = db.Column(db.String())
    content = db.Column(JSON)

    def __init__(self, note_id, user_id, module, content):
        self.note_id = note_id
        self.user_id = user_id
        self.module = module
        self.content = content

    def __repr__(self):
        return '<id {}>'.format(self.note_id)

    def as_json(self):
        return {'id': self.note_id,
                'notes': self.content}


class Assignments(db.Model):
    __tablename__ = 'assignments'

    assign_id = db.Column(db.String(), primary_key=True)
    user_id = db.Column(db.String(), ForeignKey('users.user_id'))
    module = db.Column(db.String())
    date = db.Column(db.Date())
    complete = db.Column(db.Boolean())
    content = db.Column(JSON)

    def __init__(self, assign_id, user_id, module, date, complete, content):
        self.assign_id = assign_id
        self.user_id = user_id
        self.module = module
        self.date = date
        self.complete = complete
        self.content = content

    def __repr__(self):
        return '<id {}>'.format(self.assign_id)

    def as_json(self):
        return {'id': self.assign_id,
                'deadline': (self.date - date(1970, 1, 1)).total_seconds(),
                'complete': self.complete,
                'assignmentDescription': self.content
                }
