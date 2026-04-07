import requests
import datetime
import uuid
import time
from flask import Flask, request, jsonify
from grid_measurements.src.connector.Smart_grid.functions.sm.tobeimplemented import pruefe_Steuerbefehl_moeglich, sende_steuerbefehl_an_Steuerbox

def create_app():
    app = Flask(__name__)

    @app.route('/steuerbefehl/konfiguration/', methods=['POST'])
    def konfiguration():
        location_id = request.args.get('locationID')  # Get locationID from query params
        data = request.get_json()

        if not data or not request.headers.get('Content-Type'):
            return jsonify({"error": "Ungültige Anfrage"}), 400

        print(f"Empfangene Steuerbefehl-Bestellung: {data}")
        
        # Simuliere Verarbeitung und sende Nachricht zurück an LF/NB
        state, reason = pruefe_Steuerbefehl_moeglich()  # Beispielzustand

        current_datetime = datetime.datetime.now(datetime.timezone.utc)
        creationdatetime = current_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        if state == "possible":
            preliminaryResultPositive = dict()
            preliminaryResultPositive["preliminaryStatePostive"] = state

            send_vorlaeufigePositiveAntwort(
                transaction_id=str(uuid.uuid4()),
                creationdatetime=creationdatetime,
                initial_transaction_id=request.headers.get('initialTransactionId'),
                reference_id=request.headers.get('transaction_id'),
                location_id=location_id,
                preliminaryResultPositive=preliminaryResultPositive,
                host="127.0.0.1",  # LF/NB-Server-Adresse
                port=8081  # LF/NB-Port
            )

            result = sende_steuerbefehl_an_Steuerbox()

            resultPositive = dict()
            resultPositive["statePositive"] = result

            send_positiveAntwort(
                transaction_id=str(uuid.uuid4()),
                creationdatetime=creationdatetime,
                initial_transaction_id=request.headers.get('initialTransactionId'),
                reference_id=request.headers.get('transaction_id'),
                location_id=location_id,
                resultPositive=resultPositive,
                host="127.0.0.1",  # LF/NB-Server-Adresse
                port=8081  # LF/NB-Port
            )    

        if state == "not_possible":
            reason = "communication_failure"  # Beispielgrund

            resultNegative  = dict()
            resultNegative["stateNegative"] = "Failed"
            resultNegative["reasonNegative"] = reason
        
            send_vorlaeufigeNegativeAntwort(
                transaction_id=str(uuid.uuid4()),
                creationdatetime=creationdatetime,
                initial_transaction_id=request.headers.get('initialTransactionId'),
                reference_id=request.headers.get('transaction_id'),
                location_id=location_id,
                resultNegative=resultNegative,
                host="127.0.0.1",  # LF/NB-Server-Adresse
                port=8081  # LF/NB-Port
            )

            time.sleep(5) # Simuliere Verarbeitungszeit
            resultNegative  = dict()
            resultNegative["stateNegative"] = "Failed"
            resultNegative["reasonNegative"] = reason

            send_negativeAntwort(
                transaction_id=str(uuid.uuid4()),
                creationdatetime=creationdatetime,
                initial_transaction_id=request.headers.get('initialTransactionId'),
                reference_id=request.headers.get('transaction_id'),
                location_id=location_id,
                resultNegative=resultNegative,
                host="127.0.0.1",  # LF/NB-Server-Adresse
                port=8081  # LF/NB-Port
            )

        return jsonify({"status": "Steuerbefehl-Bestellung empfangen", "data": data}), 200

    def send_vorlaeufigePositiveAntwort(
        transaction_id: str,
        creationdatetime: datetime,
        initial_transaction_id: str,
        reference_id: str,
        location_id: str,
        preliminaryResultPositive: dict,
        host: str,
        port: int
        ):
        # Ensure creationdatetime is a datetime object
        if isinstance(creationdatetime, str):
            creationdatetime = datetime.datetime.fromisoformat(
                creationdatetime.replace('Z', '+00:00')
                )

        # Convert datetime objects to strings
        creationdatetime_str = creationdatetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        # server url, die über die MAKO erhalten wurde
        url = f"http://{host}:{port}/steuerbefehl/vorlaeufigePositiveAntwort/" \
            f"?locationID={location_id}"
        payload = preliminaryResultPositive # no payload in the control command
        headers = {'accept': '*/*',
                'transaction_id': transaction_id,
                'creationdatetime':creationdatetime_str,
                'initialTransactionId': initial_transaction_id,
                'Content-Type':'application/json'}

        try:
            response = requests.post(url, json=payload, headers=headers)
            print("Response: ", response)
            return response.status_code, response.json()
        except Exception as e:
            print(f"Fehler beim Senden der Mitteilung zum weiteren Vorgehen: {e}")
            return None, {"error": str(e)}
        
    def send_vorlaeufigeNegativeAntwort(
        transaction_id: str,
        creationdatetime: datetime,
        initial_transaction_id: str,
        reference_id: str,
        location_id: str,
        resultNegative: dict,
        host: str,
        port: int
        ):
        # Ensure creationdatetime is a datetime object
        if isinstance(creationdatetime, str):
            creationdatetime = datetime.datetime.fromisoformat(
                creationdatetime.replace('Z', '+00:00')
                )

        # Convert datetime objects to strings
        creationdatetime_str = creationdatetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        # server url, die über die MAKO erhalten wurde
        url = f"http://{host}:{port}/steuerbefehl/vorlaeufigeNegativeAntwort/" \
            f"?locationID={location_id}"
        payload = resultNegative # no payload in the control command
        headers = {'accept': '*/*',
                'transaction_id': transaction_id,
                'creationdatetime':creationdatetime_str,
                'initialTransactionId': initial_transaction_id,
                'Content-Type':'application/json'}

        try:
            response = requests.post(url, json=payload, headers=headers)
            print("Response: ", response)
            return response.status_code, response.json()
        except Exception as e:
            print(f"Fehler beim Senden der Mitteilung zum weiteren Vorgehen: {e}")
            return None, {"error": str(e)}
    
    def send_positiveAntwort(
        transaction_id: str,
        creationdatetime: datetime,
        initial_transaction_id: str,
        reference_id: str,
        location_id: str,
        resultPositive: dict,
        host: str,
        port: int
        ):
        # Ensure creationdatetime is a datetime object
        if isinstance(creationdatetime, str):
            creationdatetime = datetime.datetime.fromisoformat(
                creationdatetime.replace('Z', '+00:00')
                )

        # Convert datetime objects to strings
        creationdatetime_str = creationdatetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        # server url, die über die MAKO erhalten wurde
        url = f"http://{host}:{port}/steuerbefehl/positiveAntwort/" \
            f"?locationID={location_id}"
        payload = resultPositive # no payload in the control command
        headers = {'accept': '*/*',
                'transaction_id': transaction_id,
                'creationdatetime':creationdatetime_str,
                'initialTransactionId': initial_transaction_id,
                'Content-Type':'application/json'}

        try:
            response = requests.post(url, json=payload, headers=headers)
            print("Response: ", response)
            return response.status_code, response.json()
        except Exception as e:
            print(f"Fehler beim Senden der Positiven Antwort auf den Steuerbefehl: {e}")
            return None, {"error": str(e)}
        
    def send_negativeAntwort(
        transaction_id: str,
        creationdatetime: datetime,
        initial_transaction_id: str,
        reference_id: str,
        location_id: str,
        resultNegative: dict,
        host: str,
        port: int
        ):
        # Ensure creationdatetime is a datetime object
        if isinstance(creationdatetime, str):
            creationdatetime = datetime.datetime.fromisoformat(
                creationdatetime.replace('Z', '+00:00')
                )

        # Convert datetime objects to strings
        creationdatetime_str = creationdatetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        # server url, die über die MAKO erhalten wurde
        url = f"http://{host}:{port}/steuerbefehl/negativeAntwort/" \
            f"?locationID={location_id}"
        payload = resultNegative # no payload in the control command
        headers = {'accept': '*/*',
                'transaction_id': transaction_id,
                'creationdatetime':creationdatetime_str,
                'initialTransactionId': initial_transaction_id,
                'Content-Type':'application/json'}

        try:
            response = requests.post(url, json=payload, headers=headers)
            print("Response: ", response)
            return response.status_code, response.json()
        except Exception as e:
            print(f"Fehler beim Senden der Negativen Antwort auf den Steuerbefehl: {e}")
            return None, {"error": str(e)}

    return app

def run_server(host='127.0.0.1', port=5001):
    app = create_app()
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
    run_server(host, port)
