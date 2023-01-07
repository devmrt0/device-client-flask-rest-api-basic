from base64 import decode
import string
from tokenize import String
from types import NoneType
from flask import Flask, request, jsonify, make_response, request, render_template, session, flash 
import jwt
from datetime import datetime, timedelta
from functools import wraps
from utils.common import *
from utils.api_response import *
import json 










def getTokenWs(queryToken,headersToken):
    token = ""
    if(isEmpty(queryToken) != True):
        token = queryToken
    else:
        if(isEmpty(headersToken) != True):
          token = headersToken 
    return token


def verifyTokenWs(token):
    if(token == ""):
       return error(10001,"",{'token': token})
    try:
        decoded = jwt.decode(token, 'YOU_SECRET_KEY',algorithms=['RS256',], options={"verify_signature": False})
        deviceid = decoded['deviceid']
        language = decoded['language']
        return success({'deviceid': deviceid, 'language': language, 'token': token}) 
    except (RuntimeError, TypeError, NameError,ValueError) as err:
        if(err):
             if(err == 'TokenExpiredError'):
                return error(10002,"",{'token':token})
             else:
                return error(10003,"",{'token':token})         

           
