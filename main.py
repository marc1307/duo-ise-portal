from flask import Flask, session
from flask import request

import json

import ise, duo

app = Flask(__name__)
app.secret_key = 'asdf'

@app.route('/portal/gateway', methods=['GET'])
def portal():
    with open('frontend/portal/index.html','r') as file:
        index = file.read()
    
    sessionId = request.args.get('sessionId', default = 'na', type = str)

    sessionInfo = ise.getSessionInfo(sessionId)
    index = index.replace('---SessionID---', sessionId)
    index = index.replace('---IP4---', sessionInfo['ip4'])
    
    index = index.replace('---MAC---', sessionInfo['mac'])
    print("#############")
    print(sessionInfo)
    print("#############")

    session['mac'] = sessionInfo['mac']
    session['sessionId'] = sessionId
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
    return("0")

@app.route('/api/requestAccess', methods=['POST'])
def api_requestAccess():
    print("Post Data:")
    print(request.form)
    print("Session Data:")
    print(session)

    data = request.form
    host = data["host"]

    preauth = duo.preauth(username=host)
    if preauth["response"]["result"] == "deny":
        return json.dumps(preauth)

    ## select device
    print(json.dumps(preauth, indent=4))
    for device in preauth["response"]["devices"]:
        if device["type"] == "phone":
            if 'push' in device["capabilities"]:
                print("sending push to {}".format(device["display_name"]))
                auth = duo.auth_push(username=host, device=device['device'])
                print(json.dumps(auth, indent=4))

                out = { "success": True }
                out["data"] = auth
                #return json.dumps(out)

                txid=auth["response"]["txid"]
                StopLoop = False
                while(not StopLoop):
                    r = duo.auth_status(txid)
                    if (r['response']['result'] != "waiting"):
                        print("New Status")
                        StopLoop = True
                        if (r['response']['result'] == "allow"):
                            permit=True
                            msg="Permit ({} -> {})".format(r['response']['status'], r['response']['status_msg'])
                            id=ise.findEndpointByMac(session['mac'])
                            ise.updateEndpointGroup(id)
                        else:
                            permit=False
                            msg="Deny ({} -> {})".format(r['response']['status'], r['response']['status_msg'])
                    else:
                        print("Request Allowed ({} -> {})".format(r['response']['status'], r['response']['status_msg']))

                out = { "success": True }
                out["data"] = auth
                out["status"] = msg
                return json.dumps(out)

            else:
                return json.dumps({"success": False, "msg": "no push capable phone"})
        else:
            return json.dumps({"success": False, "msg": "user has no phone"})


    return "sending push to {}".format("tbd")

@app.route('/')
def hello():
    return 'Hello, World!'



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443)