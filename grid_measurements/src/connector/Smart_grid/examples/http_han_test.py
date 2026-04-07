import requests
from requests.auth import HTTPDigestAuth
from requests.adapters import HTTPAdapter
# from urllib3.poolmanager import PoolManager
# import socket

# >>> HIER DEINE KONFIGURATION FESTLEGEN <<<
IP_ADDRESS = "192.168.137.2"       # Ziel-IP
USERNAME = "Thomas"     # Benutzername für Digest-Auth
PASSWORD = "3c4d"         # Passwort für Digest-Auth
INTERFACE_IP = "192.168.137.6"      # Lokale IP-Adresse des gewünschten Interfaces (z. B. von eth0)

# Custom HTTPAdapter, um Socket an Interface-IP zu binden
class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, **kwargs):
        self.source_ip = source_ip
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_ip, 0)
        super().init_poolmanager(*args, **kwargs)

def fetch_data(ip, username, password, interface_ip):
    url = f"https://{ip}/json/realtimedata/"
    #url = f"https://{ip}/json/metering/origin/"
    #url = f"https://{ip}/json/metering/derived/"

    session = requests.Session()
    session.mount("https://", SourceIPAdapter(interface_ip))

    try:
        response = session.get(url, auth=HTTPDigestAuth(username, password), verify=False)
        if response.status_code == 200:
            print("Daten empfangen:")
            print(response.text)
        else:
            print(f"Fehler: HTTP {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Verbindungsfehler: {e}")

if __name__ == "__main__":
    fetch_data(IP_ADDRESS, USERNAME, PASSWORD, INTERFACE_IP)
