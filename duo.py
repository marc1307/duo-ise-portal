import duo_client, json
from config import DuoConfig

def apiClient():
    cfg = DuoConfig()
    duo = duo_client.client.Client(
        ikey=cfg["ikey"],
        skey=cfg["skey"],
        host=cfg["api_host"],
    )
    return duo

def ping():
    duo = apiClient()
    

def check():
    # --path /auth/v2/check --method GET
    print("tbd")

def logo():
    print("tbd")

def enroll():
    # --path /auth/v2/enroll --method POST username=marc
    print("tbd")

def enroll_status():
    print("tbd")

def preauth(username):
    # --path /auth/v2/preauth --method POST username=marc
    duo = apiClient()
    response = duo.api_call("POST", "/auth/v2/preauth", {"username":username})
    return json.loads(response[1])

def auth(username, device, factor="push", ipaddr="127.0.0.1"):
    # --path /auth/v2/auth --method POST username=marc device=xyc factor=push ipaddr=1.3.3.7 async=1
    duo = apiClient()
    response = duo.api_call("POST", "/auth/v2/auth", {"username":username,"device":device,"factor":factor,"ipaddr":ipaddr,"async":"1"})
    return json.loads(response[1])

def auth_push(username, device, factor="push", ipaddr="", type="", display_username="New Guest", mac="---TBD---", vendor="---TBD---"):
    # --path /auth/v2/auth --method POST username=marc device=xyc factor=push ipaddr=1.3.3.7 async=1
    duo = apiClient()
    response = duo.api_call("POST", "/auth/v2/auth", {"username":username,"device":device,"factor":factor,"ipaddr":ipaddr,"async":"1","display_username":"{}".format(display_username),"pushinfo":"MAC={}&Venor={}".format(mac, vendor),"type":"WiFi Access Request"})
    return json.loads(response[1])

def auth_passcode(username, passcode, factor="passcode", ipaddr=""):
    # --path /auth/v2/auth --method POST username=marc device=xyc factor=push ipaddr=1.3.3.7 async=1
    duo = apiClient()
    response = duo.api_call("POST", "/auth/v2/auth", {"username":username,"passcode":passcode,"factor":factor,"ipaddr":ipaddr})
    return json.loads(response[1])

def auth_status(txid):
    # --path /auth/v2/auth_status --method GET txid=69ea7736-2041-4454-83c0-3a0fbb0564fc
    duo = apiClient()
    response = duo.api_call("GET", "/auth/v2/auth_status", {"txid":txid})
    # print(json.dumps(json.loads(response[1]), indent=4))
    # Req will not be anwsered if status hasn't changed
    return json.loads(response[1])


## Internal

def eval_push(txid):
    StopLoop = False
    while(not StopLoop):
        r = auth_status(txid)
        if (r['response']['result'] != "waiting"):
            print("New Status")
            StopLoop = True
            if (r['response']['result'] == "allow"):
                print("Permit ({} -> {})".format(r['response']['status'], r['response']['status_msg']))
                return True
            else:
                print("Deny ({} -> {})".format(r['response']['status'], r['response']['status_msg']))
                return False
        else:
            print("Request Allowed ({} -> {})".format(r['response']['status'], r['response']['status_msg']))
            return True

if __name__ == '__main__':
    import sys, time
    user = "marc"


    # Test Run Push
    if len(sys.argv) == 1:

        # PreAuth
        r = preauth(user)
        #print(json.dumps(r, indent=4))

        # Send Auth Request:
        r = auth_push(user, device)
        # print(json.dumps(r, indent=4))
        print("Sending 2FA Request")
        txid = r["response"]["txid"]
        # print(txid)
        print("Sent 2FA Request")

        # Check if Approved
        StopLoop = False
        while(not StopLoop):
            r = auth_status(txid)
            if (r['response']['result'] != "waiting"):
                print("New Status")
                StopLoop = True
                if (r['response']['result'] == "allow"):
                    print("Permit ({} -> {})".format(r['response']['status'], r['response']['status_msg']))
                else:
                    print("Deny ({} -> {})".format(r['response']['status'], r['response']['status_msg']))
            else:
                print("Request Allowed ({} -> {})".format(r['response']['status'], r['response']['status_msg']))

    # Test Run Passcode
    if len(sys.argv) == 2:
        r = auth_passcode(user, str(sys.argv[1]))
        if (r['response']['result'] == "allow"):
            print("Permit ({} -> {})".format(r['response']['status'], r['response']['status_msg']))
        else:
            print("Deny ({} -> {})".format(r['response']['status'], r['response']['status_msg']))