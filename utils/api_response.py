import string
from tokenize import String
from types import NoneType
from flask import Flask, request, jsonify, make_response, request, render_template, session, flash 
import jwt
from datetime import datetime, timedelta
from functools import wraps
from utils.common import *
import json 




errors = {"10001":"Token must have a value for auth", 10002:"Expired",10003:"Invalid Token",10004:"Başka bir cihaz bağlanmaya çalıştığı için bağlantı kapatıldı",
10005:"This device already connected.",10006:"Cihaz bağlı olmadığı için komut cihaza gönderilemedi.",10007:"no data found.",10008:"Token Not Found in device list."
,10009: "Invalid requestid."
,10010: "Invalid device response."
,10011: "Command timeout response."
,10012: "invalid method."
,10013: "Schema Validaiton Error."
,10014: "Json body must have value."
,20015: "Dosya bulunamadı."
}


def errlist():
   return "Listelendi"

def warning(code,detail):
    return {'status': 0, 'code': code, 'detail': detail }

def error(code,detail,data,requestid):
    msg = ""
    if isEmpty(detail) == True:
      msg = errors.get(code)
    else:
      msg = detail
    if isEmpty(data) == False:
        if isEmpty(requestid) == False:
         return {'status' : -1 , 'code': code, 'detail': msg , 'data': data , 'requestid': requestid } 
        else:
         return {'status': -1 , 'code': code, 'detail': msg , 'data': data }       
    else: 
        if isEmpty(requestid) == False:
         return {'status' : -1 , 'code': code, 'detail': msg , 'data': data , 'requestid': requestid } 
        else:
         return {'status': -1 , 'code': code, 'detail': msg , 'data': data } 


def success(data,requestid):
    if isEmpty(data) == False:
        if isEmpty(requestid) == False:
         return {'status' : 1 , 'code': 0, 'detail': "OK" , 'data': data , 'requestid': requestid } 
        else:
         return {'status': 1 , 'code': 0, 'detail': "OK" , 'data': data }       
    else: 
        if isEmpty(requestid) == False:
         return {'status' : 1 , 'code': 0, 'detail': "OK" , 'data': data , 'requestid': requestid } 
        else:
         return {'status': 1 , 'code': 0, 'detail': "OK" , 'data': data } 


def error_str(code,detail,data,requestid):
    return jsonify(error(code,detail,data,requestid))         
    
def warning_str(code,detail):
    return jsonify(warning(code,detail))

def success_str(data,requestid):
    return jsonify(success(data,requestid))
