from flask import Flask, session, Response
from flask import request

import json, time

import ise, duo

app = Flask(__name__)
app.secret_key = 'asdffa'

@app.route('/portal/gateway', methods=['GET'])
def portal():
    with open('frontend/portal/index.html','r') as file:
        index = file.read()
    
    sessionId = request.args.get('sessionId', default = 'na', type = str)
    session['sessionId'] = sessionId
    
    session['status'] = "new"
    
    try:
        type(session['detail'])
    except KeyError:
        print("session['detail'] KeyError")
        session['detail'] = initSession()


    IseSessionNotFound = True
    while (IseSessionNotFound):
        sessionInfo = ise.getSessionInfo(sessionId)
        if sessionInfo != False:
            IseSessionNotFound = False
            session['foundIseSession'] = True
            print("------session['foundIseSession'] -> {}".format(session['foundIseSession']))
            session['ISE'] = sessionInfo
        else:
            time.sleep(1)

    return index

@app.route('/portal/<resource>')
def webapp(resource):
    requestedFile = "frontend/portal/{}".format(resource)
    file = open(requestedFile,"r")
    if file.mode == 'r':                            # Da fehlt noch nee Prüfung ob das File exisiert
        fileContent = file.read()
        return fileContent                          # Mimetype müsste man auch noch setzen, wenns geht
    else:
        return "kaputt"

@app.route('/api/status')
def api_status():
    status = {
        "status": session["status"],
        "detail": session["detail"]
    }
    # ISE Status
    try:
        status["ISE"] = session['ISE']
    except:
        status["ISE"] = False

    # PreAuth Status
    try:
        status["PreAuth"] = session['PreAuth']
    except:
        status["PreAuth"] = False

    # Auth Status
    try:
        status["Auth"] = session['Auth']
    except:
        status["Auth"] = False

    # Auth Status Status
    try:
        status["AuthStatus"] = session['AuthStatus']
    except:
        status["AuthStatus"] = False

    response = apiResponseSuccess(status)
    return Response(response, mimetype='application/json')

@app.route('/api/auth/preAuth')
def api_auth_preauth(methods=['POST']):
    return ""


@app.route('/api/requestAccess', methods=['POST'])
def api_requestAccess():
    print("Post Data:")
    print(request.form)

    data = request.form
    host = data["host"]

    session['PreAuth'] = False

    preauth = duo.preauth(username=host)
    print(preauth)
    session["status"] = "preauth"
    if preauth["response"]["result"] == "deny":
        session['PreAuth'] = {
            "success": False,
            "msg": preauth["response"]['status_msg']
        }
        return apiResponseError(preauth["response"]['status_msg'])

    # select device
    print(json.dumps(preauth, indent=4))
    for device in preauth["response"]["devices"]:
        if device["type"] == "phone":
            if 'push' in device["capabilities"]:
                print("sending push to {}".format(device["display_name"]))
                session['PreAuth'] = {
                    "success": True,
                    "msg": preauth["response"]["status_msg"],
                    "DeviceName": device["display_name"]
                }
                # Send Push to Authentication
                auth = duo.auth_push(username=host, device=device['device'], mac=session['ISE']['mac'])
                try: 
                    txid=auth["response"]["txid"]
                except KeyError:
                    session['Auth'] = {
                        "success": False
                    }
                else:
                    session['Auth'] = {
                        "success": True,
                        "type": "Push",
                        "txid": True
                    }

                # Check Status of Push
                StopLoop = False
                session["AuthStatus"] = {}
                while(not StopLoop):
                    r = duo.auth_status(txid)
                    print(r)
                    session["AuthStatus"]['result'] = r['response']['result']
                    if (r['response']['result'] != "waiting"):
                        StopLoop = True
                        if (r['response']['result'] == "allow"):
                            session["AuthStatus"] = {
                                "success": True,
                                "status": r['response']['result'],
                                "msg": r['response']['status_msg']
                            }
                            permit=True                            
                        else:
                            session["AuthStatus"] = {
                                "success": False,
                                "status": r['response']['status'],
                                "msg": r['response']['status_msg']
                            }
                            permit=False
                    else:
                        print("Request Allowed ({} -> {})".format(r['response']['status'], r['response']['status_msg']))

                if (permit):
                    if ise.authorizeGuest(session['ISE']['mac']):
                        session['detail']['IseEigSet'] = True
                        if ise.sendReauthCoa(server=session['ISE']['server'], mac=session['ISE']['mac']):
                            session['detail']['IseCoaSent'] = True
                    return Response(apiResponseSuccess({}), mimetype='application/json')
                else:
                    return Response(apiResponseError("rejected"), mimetype='application/json')
            else:
                return Response(apiResponseError("No Push capable device found - please use passcode"), mimetype='application/json')
        else:
            return Response(apiResponseError("No Phone found - please use passcode"), mimetype='application/json')


    return "sending push to {}".format("tbd")

@app.route('/')
def hello():
    return 'Ready to rock :)'



def initSession():
    template = {
        "foundIseSession": False,
        "preAuth": False,
        "push-sent": False,
        "push-wating": False,
        "push-allow": False,
        "push-deny": False,
        "IseEigSet": False,
        "IseCoaSent": False
    }
    return template

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