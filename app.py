import hashlib
from datetime import datetime
import os
import json

from flask import Flask, jsonify, abort, request, session
from flask_sqlalchemy import SQLAlchemy
from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)

app.secret_key = os.environ['SECRET_KEY']
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
CLIENT_ID = os.environ['CLIENT_ID']
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

DEFAULT_MODULES = json.load(open('subjects.json'))

from models import User, Notes, Assignments


def is_logged_in():
    return 'logged_in' in session and session['logged_in']


@app.route('/planar/api/v1.0/verify', methods=['POST'])
def verify():
    print(request.json)
    if not request.json or 'idtoken' not in request.json:
        abort(400)
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(request.json['idtoken'], requests.Request(),
                                              CLIENT_ID)

        # Or, if multiple clients access the backend server:
        # idinfo = id_token.verify_oauth2_token(token, requests.Request())
        # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
        #     raise ValueError('Could not verify audience.')

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # If auth request is from a G Suite domain:
        # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
        #     raise ValueError('Wrong hosted domain.')

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        session['logged_in'] = True
        session['userid'] = userid

        # Check if user exists, load defaults if not
        user = User.query.get(session['userid'])
        if user is None:
            user = User(session['userid'], DEFAULT_MODULES, 0, 0)
            db.session.add(user)
            db.session.commit()
        return jsonify({'reponse': "Successfully verified ID"})
    except ValueError:
        return jsonify({'reponse': "Invalid ID!"})
        # Invalid token


@app.route('/planar/api/v1.0/modules', methods=['POST', 'GET'])
def subject():
    if not is_logged_in():
        return jsonify({'reponse': "Not Logged in!"})
    user = User.query.get(session['userid'])
    if request.method == 'POST':
        if request.is_json:
            user.modules = request.json
            db.session.add(user)
            db.session.commit()
            return jsonify({'reponse': "Updated modules for user " + session['userid']})
        return jsonify({'reponse': 'Invalid request!'})
    if request.method == 'GET':
        return jsonify(user.modules)


@app.route('/planar/api/v1.0/assignments/<mod>', methods=['POST', 'GET'])
def assign(mod):
    if not is_logged_in():
        return jsonify({'reponse': "Not Logged in!"})
    user = User.query.get(session['userid'])
    if request.method == 'POST':
        if request.is_json:
            for id in request.json:
                assignment_obj = Assignments.query.get(id)
                assignment_data = request.json[id]
                if assignment_obj is not None:
                    assignment_obj.date = datetime.utcfromtimestamp(assignment_data['date'])
                    assignment_obj.complete = assignment_data['complete']
                    assignment_obj.content = assignment_data['content']
                else:
                    assignment_obj = Assignments(
                        id,
                        session['userid'],
                        mod,
                        datetime.utcfromtimestamp(assignment_data['date']),
                        assignment_data['complete'],
                        assignment_data['content']
                    )
                db.session.add(assignment_obj)
                db.session.commit()
            return jsonify({'reponse': "Updated assignments for user " + session['userid']})
        return jsonify({'reponse': 'Invalid request!'})
    if request.method == 'GET':
        response = {}
        for ass in user.assignments:
            if ass.module == mod:
                response[ass.assign_id] = ass.asJson()
        return json.dumps(response)


@app.route('/planar/api/v1.0/notes/<mod>', methods=['POST', 'GET'])
def notes(mod):
    if not is_logged_in():
        return jsonify({'reponse': "Not Logged in!"})
    user = User.query.get(session['userid'])
    if request.method == 'POST':
        if request.is_json:
            for id in request.json:
                note_obj = Notes.query.get(id)
                note_data = request.json[id]
                if note_obj is not None:
                    note_obj.content = note_data['content']
                else:
                    note_obj = Notes(id, session['userid'], mod, note_data['content'])
                db.session.add(note_obj)
                db.session.commit()
            return jsonify({'reponse': "Updated notes for user " + session['userid']})
        return jsonify({'reponse': 'Invalid request!'})
    if request.method == 'GET':
        response = {}
        for note in user.notes:
            if note.module == mod:
                response[note.note_id] = note.asJson()
        return json.dumps(response)


@app.route('/planar/api/v1.0/get_tele_token', methods=['GET'])
def tele_token():
    if not is_logged_in():
        return jsonify({'reponse': "Not Logged in!"})
    num = int(session['userid'], 16) ^ (int(datetime.utcnow().timestamp()) // 60 * 60)
    m = hashlib.sha1(str(num).encode('utf-8'))

    user = User.query.get(session['userid'])
    user.token = m.hexdigest()
    db.session.commit()
    return m.hexdigest()


@app.route('/planar/api/v1.0/verify_tele_token/<token>/<id>', methods=['GET'])
def tele_verify(token, id):
    user = User.query.filter_by(token=token).first()
    if user is not None:
        print(user)
        user.telegram_id = id
        db.session.commit()
        return jsonify({'reponse': "Successfully linked user " + id})
    else:
        return jsonify({'reponse': "Invalid token!"})


@app.route('/planar/api/v1.0/tele/<id>/modules', methods=['GET'])
def tele_subject(id):
    user = User.query.filter_by(telegram_id=id).first()
    return jsonify(user.modules)


@app.route('/planar/api/v1.0/tele/<id>/assignments/<mod>', methods=['GET'])
def tele_assign(id, mod):
    user = User.query.filter_by(telegram_id=id).first()
    response = {}
    for ass in user.assignments:
        if ass.module == mod:
            response[ass.assign_id] = ass.asJson()
    return json.dumps(response)


@app.route('/planar/api/v1.0/tele/<id>/notes/<mod>', methods=['GET'])
def tele_notes(id, mod):
    user = User.query.filter_by(telegram_id=id).first()
    response = {}
    for note in user.notes:
        if note.module == mod:
            response[note.note_id] = note.asJson()
    return json.dumps(response)


@app.route('/set/<id>')
def set_dummy(id):
    session['userid'] = id
    session['logged_in'] = True
    user = User.query.get(session['userid'])
    if user is None:
        user = User(session['userid'], DEFAULT_MODULES, 0, 0)
        db.session.add(user)
        db.session.commit()
    return jsonify({'reponse': 'set id to ' + session['userid']})


@app.route('/getid')
def getid():
    return jsonify({'reponse': 'id is ' + session['userid']})


@app.route('/planar/api/v1.0/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('userid', None)
    return jsonify({'reponse': "Success"})


if __name__ == '__main__':
    app.run(debug=True)

# @app.route('/planar/api/v1.0/assignments', methods=['POST', 'GET'])
# def assignment():
#     if not is_logged_in():
#         return jsonify({'reponse': "Not Logged in!"})
#     user = User.query.get(session['userid'])
#     if request.method == 'POST':
#         if request.is_json:
#             data = request.get_json()
#             if user is not None:
#                 user.assignments = request.json
#                 db.session.add(user)
#                 db.session.commit()
#                 return jsonify({'reponse': "Updated assignments for user " + session['userid']})
#             else:
#                 new_user = User(session['userid'], '', request.json)
#                 db.session.add(new_user)
#                 db.session.commit()
#                 return jsonify({'reponse': "Created new user " + session['userid']})
#         return jsonify({'reponse': 'Invalid request!'})
#     if request.method == 'GET':
#         if user is not None:
#             return jsonify(user.assignments)
#         else:
#             user = User(session['userid'], '', '')
#             db.session.add(user)
#             db.session.commit()
#             return jsonify(user.assignments)
