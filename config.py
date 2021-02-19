import configparser

def DuoConfig():
    config = configparser.ConfigParser()
    config.read('config.ini')

    return config["Duo"]

def IseConfig():
    config = configparser.ConfigParser()
    config.read('config.ini')

    return config["ISE"]
