import logger
import logging
import DB
import argparse
from ClientHandling import *
from flask import Flask, jsonify, request, render_template
from colorama import init, Fore, Style
from datetime import timedelta
import threading
import time
init()

ClientCount = 0

StatUpdateInterval = 60

ServerInfo = F"{Fore.WHITE}[{Fore.MAGENTA}Server Info{Fore.WHITE}]{Fore.MAGENTA}"

app = Flask(__name__)

parser = argparse.ArgumentParser(description="Options:")

parser.add_argument('--suppressWarn', action='store_true', help='Suppress warning messages (Only use this if you really know what you are doing!)')
args = parser.parse_args()

DB.SuppressWarnings = args.suppressWarn

LastServerStatUpdate = time.time()

DB.start_db()
DB.get_server_stats()

def ClientCleaner():
    try:
        while not stop_event.is_set():
            clients = Client.GetClients()
            now = datetime.datetime.now()
            
            for client in clients:
                if (now - client.LastHeartbeat).total_seconds() >= 60:
                    logger.loggingInfo(f"Killed client: {client.ClientNumber} Last heartbeat was: {(now - client.LastHeartbeat).total_seconds()} ago")
                    client.ReleaseClientNumber()
            time.sleep(1)
    except Exception as e:
        logger.loggingError(f"Exception in ClientCleaner: {e}")

stop_event = threading.Event()

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

Current_Urls = []

ClientList = []

previous_time = datetime.datetime(2024, 4, 5, 12, 0, 0)
StatValues = [0, 0, 0, 0]

@app.route('/query', methods=['GET'])
async def query():
    url = DB.get_unchecked_url()
    if url != None:
        response = {'url': url}
        return jsonify(response)
    return

@app.route('/update', methods=['POST'])
async def update():
    start_time = time.perf_counter()
    data = request.get_json()
    url = data.get('url', '')
    old_url = data.get('old_url', '')
    client_id = data.get('Client', '')
    client = Client.GetClient(str(client_id))
    if client == None:
        logger.loggingWarning(f"Client '{client_id}' does not exsist!")
        return ""
    client.UpdateHeartbeat()
    Current_Urls.insert(0, url)

    if len(Current_Urls) > 14:
        Current_Urls.pop()
    try:    
        output, output2 = DB.insert_into_sites(old_url, url, client_id)
        print(time.perf_counter() - start_time)
        return output.replace("\n", "")
    except Exception as e:
        print("returing Nothing:", e)
        return ""

@app.route('/update_checked_urls', methods=['POST'])
async def update_checked_urls_route():
    data = request.json
    global checked_urls
    checked_urls = data.get('checked_urls', [])
    DB.update_checked_status(data.get('checked_urls', []))
    return "Ok"

@app.route('/newclient', methods=['GET'])
async def newclient():
    NewClient = Client(datetime.datetime.now(), str(request.remote_addr))
    ClientList.append(NewClient)
    response = {'Client': str(NewClient.ClientNumber)}
    logger.loggingInfo(f"Registered Client: {NewClient.ClientNumber} At: {request.remote_addr}")
     
    return jsonify(response)


@app.route('/disconnect', methods=['POST'])
async def disconnect():
    data = request.json
    Disconnect_ID = data.get('ID', [])
    Disconnect_Url = data.get('URL', [])
    logger.loggingInfo(f"Clinet {Disconnect_ID} disconnected, rechecking {Disconnect_Url}")
    return "Ok"

@app.route('/reconnect', methods=['POST'])
async def reconnect():
    data = request.json
    Client_ID = data.get('client', [])
    NewClient = Client(datetime.datetime.now(), str(request.remote_addr), str(Client_ID))
    ClientList.append(NewClient)
    response = {'Client Restored': str(Client_ID)}
    return jsonify(response)

def runFlask():
    app.run(host='0.0.0.0', port=27016)

if __name__ == '__main__':
    background_thread = threading.Thread(target=ClientCleaner)
    background_thread.start()

    runFlask()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Closing Server")
        stop_event.set()
        background_thread.join()
        import os
        os._exit(0)

