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

def StatChecker():
    last_checked = time.time()

    while not stop_event.is_set():

        current_time = time.time()
        if (current_time - last_checked >= StatUpdateInterval) and (Client.GetClientCount() > 0):
            last_checked = current_time
            logger.loggingDebug("Updating Stats Table")
            DB.update_server_stats(Client.GetClientCount())
            global Web_Logged_Count, Web_Searched_Count, Connected_Clients, Timestamp
            Web_Logged_Count, Web_Searched_Count, Connected_Clients, Timestamp = DB.get_server_stats()

def ClientCleaner():
    try:
        while not stop_event.is_set():
            clients = Client.GetClients()
            now = datetime.datetime.now()
            
            for client in clients:
                if (now - client.LastHeartbeat).total_seconds() >= 60:
                    logger.loggingInfo(f"Killed client: {client.ClientNumber} Last heartbeat was: {(now - client.LastHeartbeat).total_seconds()} ago")
                    client.ReleaseClientNumber()
                    #del Client.clients[client.ClientNumber]
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

def UpdateStats():
    global previous_time
    global StatValues
    current_time = datetime.datetime.now()
    time_difference = current_time - previous_time
    if time_difference.total_seconds() >= 60:
        Total_Records = DB.get_sites_count()
        Unsearched = DB.get_sites_checked()
        if Total_Records == "0" or Unsearched == "0":
            Searched_Percentage = str(0)
        else:
            Searched_Percentage = str(round(int(Unsearched) / int(Total_Records) * 100, 2))
        Searched = int(Total_Records) - int(Unsearched)
        previous_time = current_time
        StatValues[0] = Total_Records
        StatValues[1] = Unsearched
        StatValues[2] = Searched
        StatValues[3] = Searched_Percentage
    return


def time_difference(time_str):
    # Parse the input time string
    input_time = datetime.datetime.strptime(time_str, "%H:%M").time()
    
    # Get the current datetime
    now = datetime.datetime.now()
    
    # Combine the current date with the input time
    input_datetime = datetime.datetime.combine(now.date(), input_time)
    
    # If input time is in the future, adjust to previous day
    if input_datetime > now:
        input_datetime -= timedelta(days=1)
    
    # Calculate the time difference
    time_diff = now - input_datetime
    
    # Convert the time difference to a string representation
    days, seconds = time_diff.days, time_diff.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if days > 0:
        if minutes == 1:
            return f"Updated 1 day ago"
        return f"Updated {minutes} days ago"
    elif hours > 0:
        if minutes == 1:
            return f"Updated 1 hour ago"
        return f"Updated {minutes} hours ago"
    elif minutes > 0:
        if minutes == 1:
            return f"Updated 1 minute ago"
        return f"Updated {minutes} minutes ago"
    else:
        if seconds == 1:
            return f"Updated 1 second ago"
        return f"Updated {seconds} seconds ago"

# Dynamic Website Data

Web_Logged_Count = 0
Web_Searched_Count = []
Connected_Clients = []
Timestamp = []

Web_Logged_Count, Web_Searched_Count, Connected_Clients, Timestamp = DB.get_server_stats()

def timelabels():
    return ''.join(str(Timestamp))

def websites_logged():
    return Web_Logged_Count

def websites_searched():
    return Web_Searched_Count

def clients_connected():
    return Connected_Clients

def serverStats():
    serverStatInfo = [Connected_Clients[11], Web_Logged_Count[11], Web_Searched_Count[11], round((Web_Searched_Count[11] - Web_Searched_Count[10]) / (StatUpdateInterval / 60), 2)]
    return serverStatInfo

def getUpdateTimers():
    
    updateTimerData = [time_difference(Timestamp[11]), time_difference(Timestamp[11]), time_difference(Timestamp[11])]
    return updateTimerData


class URLManager:
    def __init__(self):
        self.url_array = []

    def add_entry(self, url, action):
        entry = {'url': str(action) + "@" + str(url)}
        self.url_array.append(entry)

        if len(self.url_array) > 11:
            self.url_array.pop(0)

url_manager = URLManager()

@app.route('/query', methods=['GET'])
def query():
    url = DB.get_unchecked_url()
    if url != None:
        response = {'url': url}
        return jsonify(response)
    return

@app.route('/update', methods=['POST'])
def update():
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
        url_manager.add_entry(output2, client_id)
        print(time.perf_counter() - start_time)
        return output.replace("\n", "")
    except Exception as e:
        print("returing Nothing:", e)
        return ""

@app.route('/update_checked_urls', methods=['POST'])
def update_checked_urls_route():
    data = request.json
    global checked_urls
    checked_urls = data.get('checked_urls', [])
    DB.update_checked_status(data.get('checked_urls', []))

    return "Ok"

@app.route('/newclient', methods=['GET'])
def newclient():
    NewClient = Client(datetime.datetime.now(), str(request.remote_addr))
    ClientList.append(NewClient)
    response = {'Client': str(NewClient.ClientNumber)}
    logger.loggingInfo(f"Registered Client: {NewClient.ClientNumber} At: {request.remote_addr}")
     
    return jsonify(response)


@app.route('/disconnect', methods=['POST'])
def disconnect():
    data = request.json
    Disconnect_ID = data.get('ID', [])
    Disconnect_Url = data.get('URL', [])
    #DB.update_checked_status(data.get('checked_urls', []))
    logger.loggingInfo(f"Clinet {Disconnect_ID} disconnected, rechecking {Disconnect_Url}")
    return "Ok"

@app.route('/reconnect', methods=['POST'])
def reconnect():
    data = request.json
    Client_ID = data.get('client', [])
    NewClient = Client(datetime.datetime.now(), str(request.remote_addr), str(Client_ID))
    ClientList.append(NewClient)
    response = {'Client Restored': str(Client_ID)}
    return jsonify(response)


@app.route('/entries', methods=['GET'])
def entries():
    return jsonify(url_manager.url_array)

@app.route('/stats')
def stats():
    total_records = DB.get_sites_count()
    Unsearched = DB.get_sites_checked()
    Searched = int(total_records) - int(Unsearched)

    return render_template('stats.html')

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/Total_Records')
def Total_Records():
    UpdateStats()
    return str(StatValues[0])
    
@app.route('/Unsearched_Records')
def Unsearched_Records():
    UpdateStats()
    return str(StatValues[1])

@app.route('/Searched_Records')
def Searched_Records():
    UpdateStats()
    return str(StatValues[2])

@app.route('/Searched_Percentage')
def Searched_Percentage():
    UpdateStats()
    return str(StatValues[3])

@app.route('/Total_Clients')
def Total_Clients():
    return str(ClientCount)

@app.route('/Urls')
def Urls():
    return Current_Urls

# Ajax data out

@app.route('/timelabels/') 
def api_get_timelabels(): 
    return timelabels()

@app.route('/websites-logged-data/') 
def api_get_websites_logged(): 
    return websites_logged()

@app.route('/websites-searched-data/') 
def api_get_websites_searched(): 
    return websites_searched()

@app.route('/clients-connected-data/') 
def api_get_clients_connected(): 
    return clients_connected()

@app.route('/server-statistics/') 
def api_get_server_statistics(): 
    return serverStats()

@app.route('/update-timers/')
def api_get_update_timers():
    return getUpdateTimers()


def run_flask():
    app.run(host='0.0.0.0', port=27016)

if __name__ == '__main__':
    background_thread = threading.Thread(target=ClientCleaner)
    background_thread.start()

    Server_thread = threading.Thread(target=StatChecker)
    Server_thread.start()

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Closing Server")
        stop_event.set()
        background_thread.join()
        Server_thread.join()
        import os
        os._exit(0)

