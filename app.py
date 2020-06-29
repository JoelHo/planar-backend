import os

from flask import Flask, jsonify, abort, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)

app.secret_key = os.environ['SECRET_KEY']
CLIENT_ID = os.environ['CLIENT_ID']
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

from models import User


def is_logged_in():
    return 'logged_in' in session and session['logged_in']


@app.route('/planar/api/v1.0/verify', methods=['POST'])
def verify():
    if not request.json or not 'idtoken' in request.json:
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
        return jsonify({'reponse': "Successfully verified ID"})
    except ValueError:
        return jsonify({'reponse': "Invalid ID!"})
        # Invalid token


@app.route('/planar/api/v1.0/assignments', methods=['POST', 'GET'])
def assignment():
    # if not is_logged_in():
    #     return jsonify({'reponse': "Not Logged in!"})
    user = User.query.get(session['userid'])
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            if user is not None:
                user.assignments = request.json
                db.session.add(user)
                db.session.commit()
                return jsonify({'reponse': "Updated assignments for user " + session['userid']})
            else:
                new_user = User(session['userid'], '', request.json)
                db.session.add(new_user)
                db.session.commit()
                return jsonify({'reponse': "Created new user " + session['userid']})
        return jsonify({'reponse': 'Invalid request!'})
    if request.method == 'GET':
        if user is not None:
            return jsonify(user.assignments)
        else:
            user = User(session['userid'], '', '')
            db.session.add(user)
            db.session.commit()
            return jsonify(user.assignments)


@app.route('/planar/api/v1.0/modules', methods=['POST', 'GET'])
def subject():
    # if not is_logged_in():
    #     return jsonify({'reponse': "Not Logged in!"})
    user = User.query.get(session['userid'])
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            if user is not None:
                user.subjects = request.json
                db.session.add(user)
                db.session.commit()
                return jsonify({'reponse': "Updated modules for user " + session['userid']})
            else:
                new_user = User(session['userid'], request.json, '')
                db.session.add(new_user)
                db.session.commit()
                return jsonify({'reponse': "Created new user " + session['userid']})
        return jsonify({'reponse': 'Invalid request!'})
    if request.method == 'GET':
        if user is not None:
            return jsonify(user.subjects)
        else:
            user = User(session['userid'], '', '')
            db.session.add(user)
            db.session.commit()
            return jsonify(user.subjects)


@app.route('/set/<id>')
def set_dummy(id):
    session['userid'] = id
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
