from flask import Flask, jsonify, abort, request, url_for, session
from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)


@app.route('/planar/api/v1.0/verify', methods=['POST'])
def verify():
    print(request.json)
    if not request.json or not 'idtoken' in request.json:
        abort(400)
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(request.json['idtoken'], requests.Request(),
                                              'REMOVED')

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
        return jsonify({'result': True})
    except ValueError:
        return jsonify({'result': False})
        # Invalid token


@app.route('/planar/api/v1.0/logout')
def logout():
    session['logged_in'] = True
    return jsonify({'result': True})


if __name__ == '__main__':

    app.run(debug=True)
