from flask import Flask, request, jsonify
import requests
import datetime
# Flask-Server
app = Flask(__name__)

@app.route('/steuerbefehl/vorlaeufigePositiveAntwort/', methods=['POST'])
def vorlaeufigePositiveAntwort():
    location_id = request.args.get('locationID')  # Get locationID from query params
    print(f"Location ID: {location_id}")
    data = request.get_json()

    if not data or not request.headers.get('Content-Type'):
        return jsonify({"error": "Ungültige Anfrage"}), 400

    print(f"Empfangene Vorläufige positive Mitteilung zum weiteren Vorgehen: {data}")
    return jsonify({"status": "Nachricht erfolgreich empfangen"}), 200

@app.route('/steuerbefehl/vorlaeufigeNegativeAntwort/', methods=['POST'])
def vorlaeufigeNegativeAntwort():
    location_id = request.args.get('locationID')  # Get locationID from query params
    print(f"Location ID: {location_id}")
    data = request.get_json()

    if not data or not request.headers.get('Content-Type'):
        return jsonify({"error": "Ungültige Anfrage"}), 400

    print(f"Empfangene Negative Mitteilung zum weiteren Vorgehen: {data}")
    return jsonify({"status": "Nachricht erfolgreich empfangen"}), 200

@app.route('/steuerbefehl/positiveAntwort/', methods=['POST'])
def positiveAntwort():
    location_id = request.args.get('locationID')  # Get locationID from query params
    print(f"Location ID: {location_id}")
    data = request.get_json()

    if not data or not request.headers.get('Content-Type'):
        return jsonify({"error": "Ungültige Anfrage"}), 400

    print(f"Empfangene Positive Antwort auf den Steuerbefehl: {data}")
    return jsonify({"status": "Nachricht erfolgreich empfangen"}), 200

@app.route('/steuerbefehl/negativeAntwort/', methods=['POST'])
def negativeAntwort():
    location_id = request.args.get('locationID')  # Get locationID from query params
    print(f"Location ID: {location_id}")
    data = request.get_json()

    if not data or not request.headers.get('Content-Type'):
        return jsonify({"error": "Ungültige Anfrage"}), 400

    print(f"Empfangene Negative Antwort auf den Steuerbefehl: {data}")
    return jsonify({"status": "Nachricht erfolgreich empfangen"}), 200

def run_server(host='127.0.0.1', port=8081):
    app.run(host=host, port=port, debug=False, use_reloader=False)

# Client-Funktionen
def send_command_control_create(
        transaction_id: str,
        creationdatetime: datetime,
        initial_transaction_id: str,
        sr_id: str,
        command_control: dict,
        host: str,
        port: int
        ):
    # Ensure creationdatetime is a datetime object
    if isinstance(creationdatetime, str):
        creationdatetime = datetime.datetime.fromisoformat(creationdatetime.replace('Z', '+00:00'))

    # Convert datetime objects to strings
    creationdatetime_str = creationdatetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    command_control["executionTimeFrom"] = command_control["executionTimeFrom"].strftime('%Y-%m-%dT%H:%M:%SZ')
    command_control["executionTimeUntil"] = command_control["executionTimeUntil"].strftime('%Y-%m-%dT%H:%M:%SZ')

    # server url, die über die MAKO erhalten wurde
    url = f"http://{host}:{port}/steuerbefehl/konfiguration/?locationID={sr_id}"
    payload = command_control # no payload in the control command
    headers = {'accept': '*/*',
               'transaction_id': transaction_id,
               'createionDateTime':creationdatetime_str,
               'initialTransactionId': initial_transaction_id,
               'Content-Type':'application/json'}

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("Response: ", response)
        return response.status_code, response.json()
    except Exception as e:
        print(f"Fehler beim Senden des Steuerbefehls: {e}")
        return None, {"error": str(e)}

if __name__ == '__main__':
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8081
    run_server(host, port)
