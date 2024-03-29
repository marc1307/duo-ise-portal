from flask import Flask, session, Response
from flask import request
from flask_socketio import SocketIO, emit

import json, time, os, sys
from termcolor import cprint

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import ise, duo
from config import BaseConfig



config = BaseConfig()
app = Flask(__name__)
app.secret_key = config['secret']
io = SocketIO(app, cors_allowed_origins=config['url'])

# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@app.route('/portal/gateway', methods=['GET'])
def portal():
    with open('../frontend/portal/index.html','r') as file:
        index = file.read()
    return index

@app.route('/portal/<resource>')
def webapp(resource):
    requestedFile = "../frontend/portal/{}".format(resource)
    
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
    cprint("websocket connected (ID: {})".format(request.sid), "red")
    io.emit("debug", request.sid, room=session['socketsid'])


@io.on('init') # Send ISE Session ID
def handle_init(data):
    # Regex for valid session ID /[0-9a-f]{24}/
    cprint('init - received id: ' + data, "red")
    sessionId = data
    IseSessionNotFound = True
    i = 0
    while (IseSessionNotFound and i < 10):
        sessionInfo = ise.getSessionInfo(sessionId)
        if sessionInfo != False:
            IseSessionNotFound = False
            session['foundIseSession'] = True
            cprint("------session['foundIseSession'] -> {}".format(session['foundIseSession']), "red")
            session['ISE'] = sessionInfo
            io.emit("init", {"IseSessionFound": True}, room=session['socketsid'])
            io.emit("debug", {"data": {"iseSessionData": sessionInfo}}, room=session['socketsid'])
        else:
            i = i+1
            io.emit("init", {"IseSessionFound": False}, room=session['socketsid'])
            time.sleep(1)

@io.on('auth') # Send ISE Session ID
def handle_auth(data):
    cprint('auth - received host: ' + data, "red")
    
    host = data ###### sanatize me
    session['host'] = host

    # Do Preauth
    preauth = duo.preauth(username=host)
    if preauth["response"]["result"] == "deny":
        io.emit('auth', {"module": "preauth", "success": False, "msg": preauth["response"]['status_msg']}, room=session['socketsid'])
    else:
        deviceCount = {"phone": 0, "token": 0}
        for device in preauth["response"]["devices"]:
            if device["type"] == "phone":
                deviceCount['phone'] = deviceCount['phone'] + 1
            if device["type"] == "token":
                deviceCount['token'] = deviceCount['token'] + 1
        io.emit('auth', {"module": "preauth", "success": True, "count": deviceCount}, room=session['socketsid'])
        # Search for pushable phone
        for device in preauth["response"]["devices"]:
            if device["type"] == "phone":
                if 'push' in device["capabilities"]:
                    if 'mobile_otp' in device["capabilities"]:
                        io.emit('auth', {"module": "passcode", "success": True}, room=session['socketsid'])
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
                            cprint(r, "red")
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
                                cprint("Request Allowed ({} -> {})".format(r['response']['status'], r['response']['status_msg']), "red")
            break


@io.on('auth_passcode') # Send ISE Session ID
def handle_auth_passcode(data):
    cprint('auth_passcode - received host: ' + data, "red")

    token = data
    
    r = duo.auth_passcode(session['host'], token)
    if (r['response']['result'] == "allow"):
        io.emit('auth', {"module": "auth_status", "success": True, "state": r['response']['result'], "msg": r['response']['status_msg']}, room=session['socketsid'])
        if ise.authorizeGuest(session['ISE']['mac']):
            io.emit('auth', {"module": "ise-addEig", "success": True}, room=session['socketsid'])
            if ise.sendReauthCoa(server=session['ISE']['server'], mac=session['ISE']['mac']):
                io.emit('auth', {"module": "ise-coa", "success": True}, room=session['socketsid'])
        else:
            io.emit('auth', {"module": "ise-addEig", "success": False}, room=session['socketsid'])
    else:
        io.emit('auth', {"module": "auth_status", "success": True, "state": r['response']['result'], "msg": r['response']['status_msg']}, room=session['socketsid'])


@app.route('/')
def hello():
    return 'Ready to rock :)'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443)
