import requests, json
from requests.auth import HTTPBasicAuth
from termcolor import cprint

from config import IseConfig

## omfg  XML
import xml.etree.ElementTree as ET



def getSessionInfo(IseSessionId):
    cfg = IseConfig()
    url = "https://{}/admin/API/mnt/Session/ActiveList".format(cfg["host"])
    response = requests.get(url, auth=HTTPBasicAuth(cfg["username"], cfg["password"]), verify=False)

    #tree = ET.parse('_notes/ise-mnt/2clients.xml')
    #root = tree.getroot()
    root = ET.fromstring(response.text)

    for activeSession in root.findall("./activeSession/[audit_session_id='{}']".format(IseSessionId)):
        try:
            sessionInfo = {
            "mac": activeSession.find('calling_station_id').text,
            "framed_ip_address": activeSession.find('framed_ip_address').text,
            "nas_ip_address": activeSession.find('nas_ip_address').text,
            "server": activeSession.find('server').text
        }
        except:
            return False
        return sessionInfo
    return False
    
def findEndpointByMac(mac):
    cfg = IseConfig()
    url = "https://{}:9060/ers/config/endpoint?filter=mac.EQ.{}".format(cfg["host"], mac)
    cprint("findEndpointByMac(): URL: "+url, "red")
    headers = {
        "Accept": "application/json"
    }
    response = requests.get(url, auth=HTTPBasicAuth(cfg["username"], cfg["password"]), headers=headers,verify=False)
    return json.loads(response.text)

def getEndpointById(id):
    cfg = IseConfig()
    headers = {
        "Accept": "application/json"
    }
    url = "https://{}:9060/ers/config/endpoint/{}".format(cfg["host"], id)
    response = requests.get(url, auth=HTTPBasicAuth(cfg["username"], cfg["password"]), headers=headers, verify=False)
    cprint("getEndpointById(): "+str(response.status_code), "red")
    return response.text

def getEndpointGroupId(IseEndpointGroupName):
    cfg = IseConfig()
    headers = {
        "Accept": "application/json"
    }
    if IseEndpointGroupName == "":
        cprint("getEndpointGroupId(): EPG-Name not set using 'GuestEndpoints'", "red")
        IseEndpointGroupName = "GuestEndpoints"    # System default ISE Group
    url = "https://{}:9060/ers/config/endpointgroup/name/{}".format(cfg["host"], IseEndpointGroupName)
    response = requests.get(url, auth=HTTPBasicAuth(cfg["username"], cfg["password"]), headers=headers, verify=False)
    data = json.loads(response.text)
    cprint("getEndpointGroupId(): {}".format(data['EndPointGroup']['id']), "red")
    return data['EndPointGroup']['id']


def updateEndpointGroup(id):
    cfg = IseConfig()
    if cfg["guestEndpointGroupId"] == "":
        cprint("updateEndpointGroup(): ISE EGP-Id not set. Requesting...", "red")
        cfg["guestEndpointGroupId"] = getEndpointGroupId(cfg["guestEndpointGroupName"])
    cprint("updateEndpointGroup(): Using ISE EPG with id: {} ({})".format(cfg["guestEndpointGroupId"], cfg["guestEndpointGroupName"]), "red")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "ERSEndPoint": {
            "staticGroupAssignment": True,
            "groupId": cfg["guestEndpointGroupId"]
        }
    }
    url = "https://{}:9060/ers/config/endpoint/{}".format(cfg["host"], id)
    response = requests.put(url, auth=HTTPBasicAuth(cfg["username"], cfg["password"]), headers=headers, data=json.dumps(data), verify=False)
    return json.loads(response.text)

def sendReauthCoa(server, mac, reauthType="1"):
    # Doc: https://www.cisco.com/c/en/us/td/docs/security/ise/2-4/api_ref_guide/api_ref_book/ise_api_ref_ch4.pdf
    # https://acme123/admin/API/mnt/CoA/Reauth/server12/00:26:82:7B:D2:51/1
    # 
    cfg = IseConfig()
    url = "https://{host}/admin/API/mnt/CoA/Reauth/{server}/{mac}/{reauthType}".format(host=cfg["host"],server=server,mac=mac,reauthType=reauthType)
    response = requests.get(url, auth=HTTPBasicAuth(cfg["username"], cfg["password"]), verify=False)
    cprint("sendReauthCoa(): "+response.text, "red")
    return True

def authorizeGuest(mac):
    # Get Endpoint ID by Mac
    search = findEndpointByMac(mac)
    id = search["SearchResult"]["resources"][0]["id"]

    # Add Endpoint to Guest Endpoint Group
    endpointUpdateResult = updateEndpointGroup(id)

    return True




if __name__ == '__main__':
    # getSessionInfo('fo')
    search = findEndpointByMac("5E:B4:D1:E3:D1:53")
    print(json.dumps(search, indent=4))
    id = search["SearchResult"]["resources"][0]["id"]
    print("ID: {}".format(id))
    endpoint = getEndpointById(id)
    print(json.dumps(endpoint, indent=4))

    res = updateEndpointGroup(id)

    endpoint = getEndpointById(id)
    print(json.dumps(endpoint, indent=4))