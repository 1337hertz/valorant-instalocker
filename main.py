import json
import threading
import requests
from flask import Flask, render_template, request, jsonify
from valclient.client import Client
from valclient.exceptions import HandshakeError
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon

app = Flask(__name__)
client = None
seen_matches = []

@app.route('/')
def index():
    with open('data.json', 'r') as f:
        data = json.load(f)
        agents = data['agents']
    return render_template('index.html', agents=agents)

@app.route('/lock_agent', methods=['POST'])
def lock_agent():
    global client, seen_matches
    player_region = request.form['region'].lower()
    preferred_agent = request.form['agent'].lower()

    valid_regions = ['na', 'eu', 'latam', 'br', 'ap', 'kr', 'pbe']
    if player_region not in valid_regions:
        return jsonify({'message': f"Invalid region '{player_region}'"})

    with open('data.json', 'r') as f:
        agents = json.load(f)['agents']
    
    if preferred_agent not in agents:
        return jsonify({'message': "Invalid Agent"})

    try:
        client = Client(region=player_region)
        client.activate()
    except HandshakeError as e:
        return jsonify({'message': "Unable to activate; is VALORANT running?"})

    try:
        session_state = client.fetch_presence(client.puuid)['sessionLoopState']
        if session_state == "PREGAME" and client.pregame_fetch_match()['ID'] not in seen_matches:
            client.pregame_select_character(preferred_agent)
            client.pregame_lock_character(preferred_agent)
            seen_matches.append(client.pregame_fetch_match()['ID'])
            return jsonify({'message': f'Successfully Locked {preferred_agent.capitalize()}'})
    except Exception as e:
        pass

def check_game_status():
    global client, seen_matches
    while True:
        if client is not None:
            try:
                session_state = client.fetch_presence(client.puuid)['sessionLoopState']
                if session_state == "PREGAME" and client.pregame_fetch_match()['ID'] not in seen_matches:
                    preferred_agent = request.form['agent'].lower()
                    client.pregame_select_character(preferred_agent)
                    client.pregame_lock_character(preferred_agent)
                    seen_matches.append(client.pregame_fetch_match()['ID'])
                    return f'Successfully Locked {preferred_agent.capitalize()}'
            except Exception as e:
                pass

def start_flask_server():
    app.run(debug=True, use_reloader=False)

def start_pyqt_application():
    app = QApplication([])
    viewer = QMainWindow()
    viewer.setWindowTitle("Valorant Instalocker")
    viewer.setGeometry(100, 100, 800, 600)
    viewer.setWindowIcon(QIcon("con.png")) 
    web_view = QWebEngineView(viewer)
    web_view.load(QUrl("http://127.0.0.1:5000"))
    viewer.setCentralWidget(web_view)
    viewer.show()
    app.exec_()

if __name__ == '__main__':
    threading.Thread(target=start_flask_server).start()
    start_pyqt_application()
