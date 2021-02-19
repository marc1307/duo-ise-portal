import requests, json
from requests.auth import HTTPBasicAuth

from config import IseConfig

## omfg  XML
import xml.etree.ElementTree as ET



def getSessionInfo(IseSessionId):
    print(IseSessionId)
    cfg = IseConfig()
    url = "https://{}/admin/API/mnt/Session/ActiveList".format(cfg["host"])
    print(url)
    response = requests.get(url, auth=HTTPBasicAuth(cfg["username"], cfg["password"]), verify=False)

    #tree = ET.parse('_notes/ise-mnt/2clients.xml')
    #root = tree.getroot()
    root = ET.fromstring(response.text)
    print(response.text)

    for activeSession in root.findall("./activeSession/[audit_session_id='{}']".format(IseSessionId)):
        print(activeSession)
        mac = activeSession.find('calling_station_id').text
        ip4 = activeSession.find('framed_ip_address').text
        print(mac)
        print(ip4)
        print("SES FOUND")
        return {"mac": mac, "ip4": ip4}

    print('SES NOT FOUND')
    return {"mac": "not found", "ip4": "not found"}
    
def findEndpointByMac(mac):
    cfg = IseConfig()
    url = "https://{}:9060/ers/config/endpoint?filter=mac.EQ.{}".format(cfg["host"], mac)
    print("URL: "+url)
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
    print(response.status_code)
    return response.text

def updateEndpointGroup(id):
    cfg = IseConfig()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "ERSEndPoint": {
            "staticGroupAssignment": True,
            "groupId": "aa178bd0-8bff-11e6-996c-525400b48521"
        }
    }
    url = "https://{}:9060/ers/config/endpoint/{}".format(cfg["host"], id)
    response = requests.put(url, auth=HTTPBasicAuth(cfg["username"], cfg["password"]), headers=headers, data=json.dumps(data), verify=False)

    print(response.text)
    return json.loads(response.text)

def sendCOA(sessionId):
    print("")

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