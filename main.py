from flask import Flask, session, Response
from flask import request
from flask_socketio import SocketIO, emit

import json, time

import ise, duo

app = Flask(__name__)
app.secret_key = 'asdffa'
io = SocketIO(app, cors_allowed_origins="https://wifi.schatten-it.org:8443")


import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@app.route('/portal/gateway', methods=['GET'])
def portal():
    with open('frontend/portal/index.html','r') as file:
        index = file.read()
    
    # sessionId = request.args.get('sessionId', default = 'na', type = str)
    # session['sessionId'] = sessionId
    
    # try:
    #     type(session['detail'])
    # except KeyError:
    #     print("session['detail'] KeyError")
    #     session['detail'] = initSession()


    # IseSessionNotFound = True
    # while (IseSessionNotFound):
    #     sessionInfo = ise.getSessionInfo(sessionId)
    #     if sessionInfo != False:
    #         IseSessionNotFound = False
    #         session['foundIseSession'] = True
    #         print("------session['foundIseSession'] -> {}".format(session['foundIseSession']))
    #         session['ISE'] = sessionInfo
    #     else:
    #         time.sleep(1)

    return index

@app.route('/portal/<resource>')
def webapp(resource):
    requestedFile = "frontend/portal/{}".format(resource)
    
    mimetypes = {
        "js": "application/javascript",
        "css": "text/css"
    }

    fileExtension = str(resource).rsplit(".",1)[1]
        
    file = open(requestedFile,"r")
    if file.mode == 'r':                            # Da fehlt noch nee Prüfung ob das File exisiert
        fileContent = file.read()
        if fileExtension in mimetypes:
            return Response(fileContent, mimetype=mimetypes[fileExtension])
        else:
            return Response(fileContent)                          # Mimetype müsste man auch noch setzen, wenns geht
    else:
        return "kaputt"


@io.on("connect")
def ws_connect():
    session['socketsid'] = request.sid
    io.emit("connected", room=session['socketsid'])
    print("websocket connected (ID: {})".format(request.sid))
    io.emit("debug", request.sid, room=session['socketsid'])


@io.on('init') # Send ISE Session ID
def handle_init(data):
    # Regex for valid session ID /[0-9a-f]{24}/
    print('init - received id: ' + data)
    sessionId = data
    IseSessionNotFound = True
    i = 0
    while (IseSessionNotFound and i < 10):
        sessionInfo = ise.getSessionInfo(sessionId)
        if sessionInfo != False:
            IseSessionNotFound = False
            session['foundIseSession'] = True
            print("------session['foundIseSession'] -> {}".format(session['foundIseSession']))
            session['ISE'] = sessionInfo
            io.emit("init", {"IseSessionFound": True}, room=session['socketsid'])
            io.emit("debug", {"data": {"iseSessionData": sessionInfo}}, room=session['socketsid'])
        else:
            i = i+1
            io.emit("init", {"IseSessionFound": False}, room=session['socketsid'])
            time.sleep(1)

@io.on('auth') # Send ISE Session ID
def handle_auth(data):
    print('auth - received host: ' + data)
    
    host = data ###### sanatize me


    # Do Preauth
    preauth = duo.preauth(username=host)
    print(json.dumps(preauth, indent=4))
    if preauth["response"]["result"] == "deny":
        io.emit('auth', {"module": "preauth", "success": False, "msg": preauth["response"]['status_msg']}, room=session['socketsid'])
    else:
        io.emit('auth', {"module": "preauth", "success": True}, room=session['socketsid'])
        # Search for pushable phone
        for device in preauth["response"]["devices"]:
            if device["type"] == "phone":
                if 'push' in device["capabilities"]:
                    # Send Push to Authentication
                    io.emit('auth', {"module": "preauth2", "success": True, "device": device['display_name']}, room=session['socketsid'])
                    auth = duo.auth_push(username=host, device=device['device'], mac=session['ISE']['mac'])
                    try: 
                        txid=auth["response"]["txid"]
                    except KeyError:
                        io.emit('auth', {"module": "auth", "success": False, "txid": False}, room=session['socketsid'])
                    else:
                        io.emit('auth', {"module": "auth", "success": True, "txid": True}, room=session['socketsid'])

                        StopLoop = False
                        session["AuthStatus"] = {}
                        while(not StopLoop):
                            r = duo.auth_status(txid)
                            print(r)
                            session["AuthStatus"]['result'] = r['response']['result']
                            io.emit('auth', {"module": "auth_status", 
                            "success": True, "state": r['response']['result'], "msg": r['response']['status_msg']}, room=session['socketsid'])
                            if (r['response']['result'] != "waiting"):
                                StopLoop = True
                                if (r['response']['result'] == "allow"):
                                    if ise.authorizeGuest(session['ISE']['mac']):
                                        io.emit('auth', {"module": "ise-addEig", "success": True}, room=session['socketsid'])
                                        if ise.sendReauthCoa(server=session['ISE']['server'], mac=session['ISE']['mac']):
                                            io.emit('auth', {"module": "ise-coa", "success": True}, room=session['socketsid'])
                                    else:
                                        io.emit('auth', {"module": "ise-addEig", "success": False}, room=session['socketsid'])
                            else:
                                print("Request Allowed ({} -> {})".format(r['response']['status'], r['response']['status_msg']))
            
                        
                            







def emitStatus(event, module, msg=""):
    io.emit(event, {"success": True, "module": module, "msg": msg}, room=session['socketsid'])

def emitError(event, msg):
    io.emit(event, {"success": False, "error": msg}, room=session['socketsid'])

@app.route('/')
def hello():
    return 'Ready to rock :)'

def apiResponseSuccess(data):
    if (type(data) == dict):
        out = {
            "success": True,
            "data": data
        }
        return json.dumps(out)
    else:
        exit("apiResponse(): Input Validation failed [data={}]".format(str(type(data))))

def apiResponseError(msg):
    out = {
        "success": False,
        "error": msg
    }
    return json.dumps(out)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443)