"""
API program for server
"""


from flask import Flask, jsonify, request
from flask_classful import FlaskView, route
from ClientHandling import Client
import datetime
import DB
import json
import logger
import logging
import time
import os


app = Flask(__name__)

class APIPages(FlaskView):
    def __init__(self):
        self.currentUrls = []
        self.clientList = []
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.DEBUG)

    def index(self) -> str:
        """
        Handles '/' or '/index' for a user to check the API is up
        """
        return "The API is running"
    
    def query(self) -> str:
        """
        Handles '/query' for clients to request a new URL to check
        """
        url = DB.get_unchecked_url()
        if url != None:
            response = {'url': url}
            return jsonify(response)
        return ""
    
    @route('/update', methods=['POST'])
    def update(self) -> str:
        """
        Handles '/update' for clients to provide a URL into the database
        """
        start_time = time.perf_counter()
        data = request.get_json()
        urls = data.get('url', '')
        old_url = data.get('old_url', '')
        client_id = data.get('Client', '')
        client = Client.GetClient(str(client_id))
        if client == None:
            logger.loggingWarning(f"Client '{client_id}' does not exsist!")
            return ""
        client.UpdateHeartbeat()

        try:    
            result = DB.batchUpdateUrl(connection, urls, old_url, client_id)
            logger.loggingDebug(f"Last update query took - {round(time.perf_counter() - start_time, 2)}s for {len(urls)} url(s)")
            return result
        except Exception as e:
            print("returing Nothing:", e)
            return ""
        
    @route('/update_checked_urls', methods=['POST'])
    def update_checked_urls(self) -> str:
        """
        Handles '/update_checked_urls' 
        
        When a URL is successfully checked by a client, they will provide a URL that will tell the server
        that
        """
        data = request.json
        global checked_urls
        checked_urls = data.get('checked_urls', [])
        DB.update_checked_status(data.get('checked_urls', []))
        return "Ok"
    
    def newclient(self) -> str:
        """
        Handles '/newclient'

        When a new client is created, it first asks for a client ID to be generated
        this means that each client can have their own unique signature for each
        URL 
        """
        NewClient = Client(datetime.datetime.now(), str(request.remote_addr))
        self.clientList.append(NewClient)
        response = {'Client': str(NewClient.ClientNumber)}
        logger.loggingInfo(f"Registered Client: {NewClient.ClientNumber} At: {request.remote_addr}")
        
        return jsonify(response)
    
    @route('/disconnect', methods=['POST'])
    def disconnect(self) -> str:
        """
        Handles '/disconnect'

        When a client closes their connection, they can send a disconnect packet
        so when a new client is attached, they can rescan the URL that didn't get
        scanned correctly.
        """
        data = request.json
        Disconnect_ID = data.get('ID', [])
        Disconnect_Url = data.get('URL', [])
        logger.loggingInfo(f"Clinet {Disconnect_ID} disconnected, rechecking {Disconnect_Url}")
        return "Ok"
    
    @route('/reconnect', methods=['POST'])
    def reconnect(self) -> str:
        """
        Handles '/reconnect'

        If a client disconnects because of a faulty internet connection they can
        send a reconnect packet to recreate themselves.

        WARNING - May be depreciated in next update
        """
        data = request.json
        Client_ID = data.get('client', [])
        NewClient = Client(datetime.datetime.now(), str(request.remote_addr), str(Client_ID))
        self.clientList.append(NewClient)
        response = {'Client Restored': str(Client_ID)}
        return jsonify(response)

APIPages.register(app,route_base = '/')

def generateConfig():
    """
    This generates the configuration file
    Remove this later!!!!!!!!!
    """
    if os.path.exists('./config.json'):
        configData = json.load(open("./config.json"))
        logger.loggingInfo("Reading configurations")
    else:
        logger.loggingWarning("No config file found!")
        logger.loggingInfo("Creating new config file")

        config = {
            "Database": [
                    {
                    "Type": "SQLite",
                    "Host": "127.0.0.1",
                    "Username": "user",
                    "Password": "pass",
                    "Database": "websites"
                    }
                ],
                "API": [
                    {
                        "Host": "0.0.0.0",
                        "Port": 27016
                    }
                ]
            }
        with open('./config.json', 'w') as jsonfile:
            json.dump(config, jsonfile, indent=4)

def getAPIConfig() -> dict:
    """
    Gets the API configuration from the './config.json' file

    Returns: 
        - Host: "The host the API is attached to"
        - Port: "The port the API is ran off"
    """
    if not os.path.exists('./config.json'):
        logger.loggingError("Config file not found!")
        exit()
    else:
        configData = json.load(open("./config.json"))
        APIData = configData["API"]
        return APIData[0]["Host"], APIData[0]["Port"]

def startAPI(dbconnection) -> None:
    """
    Starts the API server, 
    """
    global connection
    connection = dbconnection
    APIData = getAPIConfig()
    app.run(host=APIData[0], port=APIData[1]) 

if __name__ == '__main__':
    # Used for testing purposes
    generateConfig()
    DB.start_db()
    APIData = getAPIConfig()
    app.run(host=APIData[0], port=APIData[1]) 