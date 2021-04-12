# duo-ise-portal

## Requirements
 * Cisco Identity Services Engine (tested with 2.7 p2)
 * Duo with Auth API

## How to run:
### Configuration (config.ini):

#### Base
- Configure your Portal URL
- Add a random secret key (used for Flask session encryption)

#### ISE
- Add ISE host and credentials to config.ini
- Add Guest Endpoint Group ID

#### Duo
- Create an application in Duo Dashboard - Type: Auth API
- Add ikey, skey and api host to config.ini

### Configuration ISE:
#### Policy:
Configure regular guest flow:
1. If endpoint in guest EPG -> Permit Access
2. If not -> send the redirect

#### Authorization Profile:
- use Web Redirection in Authorization Profile and use static hostname option to redirect to the client to this portal 
- the port is set by the selected ise portal

### Run Option 1: Docker
```shell
git clone https://github.com/marc1307/duo-ise-portal.git
cd duo-ise-portal
[edit config.ini]
docker-compose pull
docker-compose up -d
```

### Run Option 2: native
```shell
git clone https://github.com/marc1307/duo-ise-portal.git
cd duo-ise-portal/backend
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py
flask run
```