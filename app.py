import os

from flask import Flask, jsonify, abort, request, url_for, session
from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)

app.secret_key = os.environ['SECRET_KEY']
CLIENT_ID = os.environ['CLIENT_ID']


def is_logged_in():
    return 'logged_in' in session and session['logged_in']


@app.route('/verify', methods=['POST'])
def verify():
    print(request.json)
    if not request.json or not 'idtoken' in request.json:
        abort(400)
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(request.json['idtoken'], requests.Request(),
                                              CLIENT_ID)
        print(idinfo)
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
        return jsonify({'result': "Success"})
    except ValueError:
        return jsonify({'result': "Invalid ID!"})
        # Invalid token


@app.route('/update_assignments', methods=['POST'])
def update():
    print(request.json)
    if is_logged_in():
        print(request.json)
        return jsonify({'result': "Success"})
    else:
        return jsonify({'result': "Not Logged in!"})


@app.route('/get_assignments', methods=['GET'])
def get():
    if is_logged_in():
        return jsonify({'result': "Success"})
    else:
        return jsonify({'result': "Not Logged in!"})


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('userid', None)
    return jsonify({'result': "Success"})


if __name__ == '__main__':
    app.run(debug=True)
