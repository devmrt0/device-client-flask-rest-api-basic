import string
from tokenize import String
from types import NoneType
from flask import Flask, request, jsonify, make_response, request, render_template, session, flash 
import jwt
from datetime import datetime, timedelta
from functools import wraps
from utils.common import *
import json 
with open("datas\devices.json") as json_file: json_data = json.load(json_file)
import sys


app = Flask(__name__)


app.config['SECRET_KEY'] = 'YOU_SECRET_KEY'





def getJWTClaims(jwtdeviceid,jwtpassword,jwtlanguage):
    deviceid = ""
    password = ""
    language = ""
    if isEmpty(jwtdeviceid) == True:
         return jsonify({'error': 'true'})
    if isEmpty(jwtpassword) == True:
         return jsonify({'error': 'true'})
    if isEmpty(jwtlanguage) == True:
         return jsonify({'error': 'true'})
    else:     
       deviceid = jwtdeviceid
       password = jwtpassword
       language = jwtlanguage 
       return jsonify({'error': 'false', 'deviceid': deviceid , 'password': password, 'language': language }) 

def authDevice(id,password):
    match = next((d for d in json_data if d['id'] == id),'false')
    passs = match.get('password')
    if match != 'false' and passs == password:
        return match
    else:
       return 'false'     




async def login():
    post_data = request.get_json()
    password = post_data.get('jwtpassword')
    deviceid = post_data.get('jwtdeviceid')
    language = post_data.get('jwtlanguage')
    result = getJWTClaims(deviceid,password,language).get_json()
    error = result.get('error')
    authh = authDevice(deviceid,password)

    if error == 'true':
        app.logger.error('An error JWT Claims')
        return make_response(jsonify({'message': 'deviceid,password,language required must be Header or Body'}), 401)

    if authh == 'false':
       app.logger.error('An error Device Auth')  
       return make_response(jsonify({'message': 'Forbidden'}), 403)   


    if error != 'true' and authh != 'false':
       
        session['logged_in'] = True

        token = jwt.encode({
            'user': deviceid,
            # don't foget to wrap it in str function, otherwise it won't work [ i struggled with this one! ]
            'expiration': str(datetime.utcnow() + timedelta(seconds=60))
        },
            app.config['SECRET_KEY'])
        return jsonify({'token': token})
    else:
        app.logger.error('An error Server')
        return make_response(jsonify({'message': 'Server Error'}), 500)
    