import logger
import DB
import argparse
from ClientHandling import *
from colorama import init
import datetime
import threading
import time
import json
import os
import asyncio
from API import getAPIConfig, app
init()


parser = argparse.ArgumentParser(description="Options:")

parser.add_argument('--suppressWarn', action='store_true', help='Suppress warning messages (Only use this if you really know what you are doing!)')
args = parser.parse_args()

DB.SuppressWarnings = args.suppressWarn

stop_event = threading.Event()


def ClientCleaner() -> None:
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
    return

def generateConfig() -> None:
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
    return

def handleAPI() -> None:
    """
    Handles the API through the Flask framework
    """
    APIData = getAPIConfig()
    app.run(host=APIData[0], port=APIData[1]) 
    return


async def main():
    # Start the client cleaner to manage heartbeats
    cleanerThread = threading.Thread(target=ClientCleaner, daemon=True)
    cleanerThread.start()

    # Prepare configurations and database
    generateConfig()
    DB.start_db()
    DB.get_server_stats()

    # Start API
    flaskThread = threading.Thread(target=handleAPI, daemon=True)
    flaskThread.start()
    
    
    try:
        while True:
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Closing Server")
        stop_event.set()
        cleanerThread.join()
        import os
        os._exit(0)


if __name__ == "__main__":
    asyncio.run(main())
