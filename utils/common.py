import string
from tokenize import String
from types import NoneType
from flask import Flask, request, jsonify, make_response, request, render_template, session, flash 
import jwt
from datetime import datetime, timedelta
from functools import wraps


def isEmptyValue(val):
    if type(val) == NoneType or val is None: 
        return True
    else: 
        return False


def isEmptyString(val):
    if (type(val) == str and (val == "" or val == '')): 
        return True
    else: 
        return False


def isEmpty(val):
    if isEmptyValue(val) == True or isEmptyString(val) == True:
        return True
    else:
        return False     