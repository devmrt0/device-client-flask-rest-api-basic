from hashlib import new
from imaplib import Commands
import string
from tokenize import String
from types import NoneType
from wsgiref import validate
from flask import Flask, request, jsonify, make_response, request, render_template, session, flash 
import jwt
import uuid
from datetime import datetime, timedelta
from functools import wraps
from utils.common import *
from utils.api_response import *
from utils.wstoken import *
from utils.json_schema import *
import json 
with open("./datas/devices.json") as json_file: json_data = json.load(json_file)
with open("./datas/screen.json") as screen_file: screen_data = json.load(screen_file)
with open("./datas/whitelist.json") as whitelist_file: whitelist_data = json.load(whitelist_file)
with open("./datas/screen.json", 'r', encoding='utf-8') as screen_filee: screen_data2 = json.load(screen_filee)
with open("./datas/commands.json") as commands_file: commands_data = json.load(commands_file)
with open("./datas/tokens.json") as token_file: token_data = json.load(token_file)
import sys
import websocket
import _thread
import time
from promise import Promise
import threading
import asyncio
import rel
from time import sleep,process_time
import sched
import schedule








app = Flask(__name__)


def on_message(ws, message):
    print(message)
    return 'true'

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")   
#wss://api.gemini.com/v1/marketdata/btcusd?top_of_book=true&bids=false
#ws://echo.websocket.events
#wss://api.gemini.com/v2/marketdata/btcusd?top_of_book=true&bids=false

websocket.enableTrace(True)
ws = websocket.WebSocketApp("wss://api.gemini.com/v2/marketdata/btcusd?top_of_book=true&bids=false",on_open=on_open,on_message=on_message,on_error=on_error,on_close=on_close)

ws.run_forever(dispatcher=rel)  # Set dispatcher to automatic reconnection
#rel.signal(2, rel.abort)  # Keyboard Interrupt
#rel.dispatch()
    
#websocket.enableTrace(True)
#ws = websocket.WebSocket()
#ws.connect("wss://api.gemini.com/v2/marketdata/btcusd?top_of_book=true&bids=false")
#ws.send("Hello, Server")
#print(ws.recv())


                    


# -------------------------------------------------------------------------- AUTH ---------------------------------------------------------------------- 


app.config['SECRET_KEY'] = 'YOU_SECRET_KEY'

def Verifytoken(func):
    # decorator factory which invoks update_wrapper() method and passes decorated function as an argument
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization').split(" ")[1]
        if not token:
            return jsonify({'Alert!': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],algorithms=['RS256',], options={"verify_signature": False})
           
        except jwt.DecodeError:
            return jsonify({'Message': 'Invalid token'}), 401
        return func(*args, **kwargs)
    return decorated


def VerifytokenAsync(func):
    # decorator factory which invoks update_wrapper() method and passes decorated function as an argument
    @wraps(func)
    async def decorated(*args, **kwargs):
        token = request.headers.get('Authorization').split(" ")[1]
        if not token:
            return jsonify({'Alert!': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],algorithms=['RS256',], options={"verify_signature": False})
           
        except jwt.DecodeError:
            return jsonify({'Message': 'Invalid token'}), 401
        await asyncio.sleep(0.1)
        return await func(*args, **kwargs)
    return decorated    


@app.route('/')
def home():
    if not session.get('logged_in'):
        return "NOT LOGGED!"
    else:
        return 'logged in currently'

# Just to show you that a public route is available for everyone
@app.route('/public')
def public():
    return "public"

# auth only if you copy your token and paste it after /auth?query=XXXXXYour TokenXXXXX
# Hit enter and you will get the message below.
@app.route('/auth')
@Verifytoken
def auth():
    return 'JWT is verified. Welcome to your dashboard !  '

# Login page


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

            



@app.route('/login', methods=['GET','POST'])
async def login():
    post_data = request.get_json()
    password = post_data.get('jwtpassword')
    deviceid = post_data.get('jwtdeviceid')
    language = post_data.get('jwtlanguage')
    result = getJWTClaims(deviceid,password,language).get_json()
    error = result.get('error')
    authh = authDevice(deviceid,password)

    if error == 'true':
        
        return make_response(jsonify({'message': 'deviceid,password,language required must be Header or Body'}), 401)

    if authh == 'false':  
       return make_response(jsonify({'message': 'Forbidden'}), 403)   


    if error != 'true' and authh != 'false':
       
        session['logged_in'] = True

        token = jwt.encode({
            'user': deviceid,
             # dont forget to wrap it in str function, otherwise it won't work [ i struggled with this one! ]
            'expiration': str(datetime.utcnow() + timedelta(seconds=60))
        },
            app.config['SECRET_KEY'])
        return jsonify({'token': token})
    else:
        return make_response(jsonify({'message': 'Server Error'}), 500)


   # -------------------------------------------------------------------------- AUTH ---------------------------------------------------------------------- 


   # -------------------------------------------------------------------------- DEVICE ---------------------------------------------------------------------- 
   
   # ------- Commands models

async def getCommand(url,http_method,method_type):
    mthd = http_method
    mthd_type = method_type
    ur = url
    match = next((d for d in commands_data if d['url'] == url),'false')
    return match

def checkDataIsArray(data):
    if len(data) !=0 and data!= None and isinstance(data,dict):
        return 'true'
    else:    
        return 'false'

async def getCommandEx(url,http_method,id,data): 
    if http_method == "post" and id == None:
        if checkDataIsArray(data) == 'true':
            return await getCommand(url,http_method,"all")
        else:
            return await getCommand(url,http_method,"id")
    else:
        if id == None:
            return await getCommand(url,http_method,"all")
        else:
            return await getCommand(url,http_method,"id")



   
   
   #--------
   
   # ------- Device models

class Device():
    commands = {}
    def __init__(self, id, language, token):
        self.id = id
        self.language = language
        self.token = token
        
        


    async def sendCommand(method,data):
        command = {}
        s1 = Device
        command['status'] = 0
        command['code'] = 0
        command['detail'] = "OK"
        command['method'] = method
        command['requestid'] = uuid.uuid4()
        command['data'] = {}
        if isEmpty(data) == False:
            command['data'] = data
            s1.commands['requestid'] = command['requestid']
            s1.commands['command'] = command
            ws.send(str(jsonify({'method': command['method'], 'requestid': command['requestid'], 'data': command['data']})))
            #ws.recv()
            return command
        else:
             ws.send(str(jsonify({'method': command['method'], 'requestid': command['requestid']}))) 
             #ws.recv()
             s1.commands['requestid'] = ""
             s1.commands['command'] = "" 
             del command['data']
             return command['requestid']

    
async def addCommand(method,data):
    try:
       requestid = await Device.sendCommand(method,data)
       comm = Device.commands['requestid']
       result = comm
       if comm == "":
            result = error(10011,"","","")
       else:
            result = comm 
  
       if(result != ""):
        
         del Device.commands['requestid']
         return result
       else:
       
         del Device.commands['requestid']
         return 'Error'  
    except TypeError as err:
        return { 'message': "Server Error. " + str(err) }

async def timeRepeatCommand(method,data):
    requestid = await addCommand(method,data)
    t = threading.Timer(5, timeRepeatCommand,[method,data])
    t.start()
    t1_start = process_time()
    print ("Hello, World!")
    print(t)
    if t1_start > 10.0:
      t.cancel()
      return requestid
    elif (t1_start < 10.0) and (requestid == "" or requestid == 'Error'):
        t.join()
        
            

       
        






def parseResponseMessage(msg):
    try:
        com = json.loads(msg)
        if isEmpty(com["requestid"]) == True:
            return error_str(10010)
        else:
            return success(com["data"], com["requestid"])
    except ValueError as err:
        return error_str(10010, "", {"error": err})



def processCommand(msg):
    result = parseResponseMessage(msg)
    if (isEmpty(result['requestid']) == False):
        command = next((d for d in commands_data if d['requestid'] == result['requestid']),'false')
        if(type(command) != None):
            command['status'] = result['status']
            command['code'] = result['code']
            command['detail'] = result['detail']
            if(type(result['data'])):
               command['data'] = result['data']
            return success_str()
        else:
            return error_str(10009,"",None,result['requestid'])
    else:
        return error_str(10010)             




class Devices():
    TokenList = {}
    DeviceList = {}
    def __init__(self,commands):
       self.commands = commands          
    

    def hasByToken(tokens):
        device = next((token for token in Devices.TokenList.items() if token == tokens), None)
        return device

    def hasByDeviceid(deviceids):
        device = next((deviceid for deviceid in Devices.DeviceList.items() if deviceid == deviceids), None)
        return device    

    async def checkDataIsNull(data):
        if (data == None or data == ""):
            return {'data':{}}
        else:
            return data 
    
    def AddToData(data,value,url):
        if (data == None):
            data = {}
        if(url == 'black_list'):
            data['uniqueid'] = value    
        else:
            data['id'] = value
        return data 
    
    def addDat(id,token,language,ws):
        device = Device(id,token,language,ws)
        Devices.TokenList['token'] = token
        Devices.TokenList['device'] = device
        Devices.DeviceList['id'] = id
        Devices.DeviceList['device'] = device
        return True              

    def deleteByToken(tokens):
         device = next((token for token in Devices.TokenList.items() if token == tokens), None)
         if(device != None):
            del Devices.DeviceList[tokens]
            del Devices.TokenList[tokens] 
            return Devices.TokenList
         else:
            return Devices.TokenList 

    def deleteByDeviceId(tokens):
         device = next((deviceid for deviceid in Devices.DeviceList.items() if deviceid == tokens), None)
         if(device != None):
            del Devices.DeviceList[tokens]
            del Devices.TokenList[tokens] 
            return Devices.DeviceList 
         else:
            return Devices.DeviceList 
    
    def deleteAndCloseByToken(tokens,msg):
          device = next((token for token in Devices.TokenList.items() if token == tokens), None)
          if (device != None):
            ws.send(msg)
            ws.close()
            Devices.deleteByToken(tokens) 
            return tokens
          else:
            return tokens

    async def queryStringIdToData(data,query,id,url):
        #if(len(query) == 0)
        if(query == None or query == "" ) and (id != None and id !=""):
            data = Devices.AddToData(data,id,url)
            return data
        else:
            data = await Devices.checkDataIsNull(data)
            if (id != None and id !=""):
                data = Devices.AddToData(data,id,url)
                for param in query:
                    data[param] = query[param]
            return data 
    
    async def validate_schema(command,data):
        if(command['json_schema'] != None):
            if(len(data) == 0):
                return {'valid': False , 'error':"Body must have a value"}
            else:
                return await SchemaValidate(data,command['json_schema']) 
        else:
            return {'valid': True, 'error':""}                                      

    async def addCommandToList(http_method,url,devicesid,query,data,id):
        command = await getCommandEx(url,http_method,id,data)
        if(command != None):
            device = next((d for d in json_data if d["id"] == devicesid), None)
            if (device != None):
                commands = await Devices.queryStringIdToData(data,query,id,url)
                vs = await Devices.validate_schema(command,commands)
                if(vs['valid'] == True):
                    return error(10013,"","Validation Error","") 
                    #addCommand(command['method_name'],commands)
                else:
                  return error(10013,"","Validation Error","")
            else:                                          
                return error(10006,"","","")
        else:
            return error(10012,"","","")        

    def processCommandDevices(tokens,msg):
        device = next((t for t in token_data if ['token'] == tokens), None)
        if (device != None):
            return processCommand(msg)
        else:
            return error_str(10008,"Token not Found in Device List",{'token': tokens},"")    

    
    
    
    
    
    
                           

            
            

        
   
@app.route('/api/device/cm', methods=['GET'])
async def getCommandddsssd():
     result = await timeRepeatCommand("get_device_status",None)
     return make_response(jsonify({'result': result}), 200)   
                





   #--------

@app.route('/api/device/<device_id>/<command>', methods=['GET'])
@VerifytokenAsync
async def getCommandAll(device_id,command):
    try:
        result = await Devices.addCommandToList('get',command,device_id,None,None,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)

    

      



@app.route('/api/device/<device_id>/<string:command>/<id>', methods=['GET'])
@VerifytokenAsync
async def getCommandById(device_id,command,id):
    try:
        result = await Devices.addCommandToList('get',command,device_id,"",None,id)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except:
         return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/device/<device_id>/<command>', methods=['POST'])
@VerifytokenAsync
async def postCommandAll(device_id,command):
    try:
        post_data = request.get_json()
        result = await Devices.addCommandToList('post',command,device_id,None,post_data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500) 



@app.route('/api/device/<device_id>/<string:command>/<id>', methods=['POST'])
@VerifytokenAsync
async def postCommandById(device_id,command,id):
    try:
        post_data = request.get_json()
        result = await Devices.addCommandToList('get',command,device_id,None,post_data,id)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except:
         return make_response(jsonify({'message': 'Server Error'}), 500)        
   


@app.route('/api/device/<device_id>/<command>', methods=['DELETE'])
@VerifytokenAsync
async def deleteCommandAll(device_id,command):
    try:
        result = await Devices.addCommandToList('get',command,device_id,None,None,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500) 



@app.route('/api/device/<device_id>/<string:command>/<id>', methods=['DELETE'])
@VerifytokenAsync
async def deleteCommandById(device_id,command,id):
    try:
        result = await Devices.addCommandToList('get',command,device_id,"",None,id)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except:
         return make_response(jsonify({'message': 'Server Error'}), 500)

@app.route('/api/device/<device_id>/<command>/count', methods=['GET'])
@VerifytokenAsync
async def getCommandCountAll(device_id,command):
    try:
        result = await Devices.addCommandToList('get',command + "_count",device_id,None,None,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)

@app.route('/api/device/<device_id>/<command>/list', methods=['GET'])
@VerifytokenAsync
async def getCommandListAll(device_id,command):
    try:
        result = await Devices.addCommandToList('get',command + "_list",device_id,None,None,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500) 
   
   
@app.route('/api/device/<device_id>/user/<int:user_id>/uniqueid', methods=['GET'])
@VerifytokenAsync
async def getUserUniqueIdCommand(device_id,user_id):
    try:
        data = {'user_id': user_id}
        result = await Devices.addCommandToList('get',"user_uniqueid",device_id,None,data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/device/<device_id>/user/<int:user_id>/uniqueid', methods=['POST'])
@VerifytokenAsync
async def postUserUniqueIdCommand(device_id,user_id):
    try:
        post_data = request.get_json()
        post_data['user_id'] = user_id
        result = await Devices.addCommandToList('post',"user_uniqueid",device_id,None,post_data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/device/<device_id>/user/<int:user_id>/uniqueid', methods=['DELETE'])
@VerifytokenAsync
async def deleteUserUniqueIdCommand(device_id,user_id):
    try:
        data = {'user_id': user_id}
        result = await Devices.addCommandToList('delete',"user_uniqueid_all",device_id,None,data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/device/<device_id>/user/<int:user_id>/uniqueid/<unique_id>', methods=['DELETE'])
@VerifytokenAsync
async def deleteUserUniqueIdCommandById(device_id,user_id,unique_id):
    try:
        data = {'user_id': user_id, 'uniqueid':unique_id}
        result = await Devices.addCommandToList('delete',"user_uniqueid_all",device_id,None,data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/device/<device_id>/user/<int:user_id>/photo/profile', methods=['GET'])
@VerifytokenAsync
async def getUserProfilePhotoCommand(device_id,user_id):
    try:
        data = {'user_id': user_id}
        result = await Devices.addCommandToList('get',"user_photo_profile",device_id,None,data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/device/<device_id>/user/<int:user_id>/photo/profile', methods=['POST'])
@VerifytokenAsync
async def postUserProfilePhotoCommand(device_id,user_id):
    try:
        post_data = request.get_json()
        post_data['user_id'] = user_id
        result = await Devices.addCommandToList('post',"user_photo_profile",device_id,None,post_data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500) 


@app.route('/api/device/<device_id>/user/<int:user_id>/uniqueid', methods=['DELETE'])
@VerifytokenAsync
async def deleteUserProfilePhotoCommand(device_id,user_id):
    try:
        data = {'user_id': user_id}
        result = await Devices.addCommandToList('delete',"user_photo_profile",device_id,None,data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)



@app.route('/api/device/<device_id>/user/<int:user_id>/timezone/<date>', methods=['GET'])
@VerifytokenAsync
async def getUserTzCommandByDate(device_id,user_id,date):
    try:
        data = {'user_id': user_id,'date':date}
        result = await Devices.addCommandToList('get',"user_time_zone",device_id,None,data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)         


@app.route('/api/device/<device_id>/user/<int:user_id>/timezone', methods=['GET'])
@VerifytokenAsync
async def getUserTzCommand(device_id,user_id):
    try:
        data = {'user_id': user_id , 'date':'reg.params date url de belirtilmemiş'}
        result = await Devices.addCommandToList('get',"user_time_zone_all",device_id,None,data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/device/<device_id>/user/<int:user_id>/timezone', methods=['POST'])
@VerifytokenAsync
async def postUserTzCommand(device_id,user_id):
    try:
        post_data = request.get_json()
        post_data['user_id'] = user_id
        result = await Devices.addCommandToList('post',"user_time_zone",device_id,None,post_data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)         



@app.route('/api/device/<device_id>/user/<int:user_id>/timezone/<date>', methods=['DELETE'])
@VerifytokenAsync
async def deleteUserTzCommandByDate(device_id,user_id,date):
    try:
        data = {'user_id': user_id,'date':date}
        result = await Devices.addCommandToList('delete',"user_time_zone",device_id,None,data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/device/<device_id>/user/<int:user_id>/timezone', methods=['DELETE'])
@VerifytokenAsync
async def deleteUserTzCommand(device_id,user_id):
    try:
        data = {'user_id': user_id }
        result = await Devices.addCommandToList('delete',"user_time_zone_all",device_id,None,data,None)
        if (result['status'] == None):
            return make_response(jsonify({'message': 'Server Error Undefined Error'}), 500)
        elif (result['status'] == -1) and (result['code'] == 10012 or result['code'] == 10013 or result['code'] == 10014 ):
            return make_response(jsonify({'result': result}), 400)
        else:
            return make_response(jsonify({'result': result}), 200)     
    except OSError as err:
         return make_response(jsonify({'message': 'Server Error'}), 500)                     
      
   
   
   
   
   
   
   
   
   
   
   
   
   # -------------------------------------------------------------------------- DEVICE ---------------------------------------------------------------------- 

   # -------------------------------------------------------------------------- WS ----------------------------------------------------------------------
def handleWs(reg):
    try:
        result = verifyTokenWs(getTokenWs(reg['query']['token'],reg['header']['token']))
        if(result['status'] == -1):
           
           if(isEmpty(result['data']['token']) == False):
            Devices.deleteByToken(result['data']['token'])
           ws.send(jsonify(result))
           ws.recv()
           ws.close() 
        else: 
            if(Devices.hasByToken(result['data']['token']) != None):
                Devices.deleteAndCloseByToken(result['data']['token'],jsonify({'status':-1, 'code': 10004, 'detail': "Başka bir cihaz bağlanmaya çalıştığı için bağlantı kapatıldı.", 'data': { 'deviceid': result['data']['deviceid'], 'language': result['data']['language'], 'token': result['data']['token']}}))  
                ws.send(jsonify({'status':-1,'code': 10005, 'detail':'This Device Already Connected', 'data':{'deviceid': result['data']['deviceid'], 'language': result['data']['language'], 'token': result['data']['token']}}))
                ws.recv()
                ws.close()
                print("WebSocket disconnetcted for decice already connected")
            else:
                Devices.addDat(result['data']['deviceid'], result['data']['language'], result['data']['token'])
                ws.send(jsonify(result))
                ws.recv()
                print("WebSocket connetcted()")
    except sys.exc_info()[0] as err:
        print(err)

        
                       















   
   
   
   
   
   
   
   # -------------------------------------------------------------------------- WS ----------------------------------------------------------------------
   
   
   
   
   #------------------------------------------------------------------------------ VERIFY ---------------------------------------------------------------------

   #-----------------Models

def hasUser(id):
    match = next((d for d in whitelist_data if d['uid'] == id),'false')
    return match

def verifyUid(deviceid,uid,language):
    print(deviceid,uid,language)
    if hasUser(uid) != 'false':
     screen = getById(1)
     del screen['data']['id']
     del screen['data']['default_screen_type']
     user = next((d for d in whitelist_data if d['uid'] == uid),'false')
     screen['data']['line_1']['text'] = user['name']
     screen['data']['line_3']['text'] = user['position']  
     return screen 
    else:
        screen = getById(2)
        return screen     




def verifyFace(deviceid,uid,language):
    return "In Development(Geliştirlecek)"
       
def verifyQR(deviceid,uid,language):
    return "In Development(Geliştirlecek)"

   #----------------------
@app.route('/api/verify/uid', methods=['POST'])
@Verifytoken
def VerifyUId():
    post_data = request.get_json()
    uid = post_data.get('uid')
    deviceid = post_data.get('deviceid')
    language = post_data.get('language') 
    try:
        return make_response(jsonify(verifyUid(deviceid,uid,language)), 200)
    except:
        return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/verify/bio', methods=['POST'])
@Verifytoken
def VerifyBio():
    post_data = request.get_json()
    uid = post_data.get('uid')
    deviceid = post_data.get('deviceid')
    language = post_data.get('language') 
    try:
        return make_response(jsonify(verifyFace(deviceid,uid,language)), 200)
    except:
        return make_response(jsonify({'message': 'Server Error'}), 500)

@app.route('/api/verify/qr', methods=['POST'])
@Verifytoken
def VerifyQR():
    post_data = request.get_json()
    uid = post_data.get('uid')
    deviceid = post_data.get('deviceid')
    language = post_data.get('language') 
    try:
        return make_response(jsonify(verifyQR(deviceid,uid,language)), 200)
    except:
        return make_response(jsonify({'message': 'Server Error'}), 500)


   
   
   
   
   
   
   
   
   #------------------------------------------------------------------------------- VERIFY --------------------------------------------------------------------- 

   #------------------------------------------------------------------------------ SCREEN ---------------------------------------------------------------------

   #-----------------Models

def hasScreen(id):
    match = next((d for d in screen_data if d['id'] == id),'false')
    return match

def getById(id):
     # query içine eklenecek parametre sonra
    if hasScreen(id) != 'false':
        return success(next((d for d in screen_data if d['id'] == id),'false'),"")
    else:
        return warning(10007,"") 

def getAll():
    # query içine eklenecek parametre sonra
    if len(screen_data2) == 0:
       return warning(10007,"")
    else:
       return success(screen_data2,"")            

 




   #----------------------


@app.route('/api/screen')
@Verifytoken
def getScreenAll():
    try:
       return make_response(jsonify(getAll()), 200)
    except:
        return make_response(jsonify({'message': 'Server Error'}), 500)


@app.route('/api/screen/<int:scr_id>')
@Verifytoken
def getScreenById(scr_id):
    try:
       return make_response(jsonify(getById(scr_id)), 200)
    except:
        return make_response(jsonify({'message': 'Server Error'}), 500)        


       
 
        
            
        
    

   
   
   
   
   
   
   
   
   #------------------------------------------------------------------------------- SCREEN --------------------------------------------------------------------- 





            
    







if __name__ == "__main__":
    app.run(debug=True)
    