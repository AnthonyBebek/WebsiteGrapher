from typing import Union
from fastapi import FastAPI, Request
import FastDB as DB
from ClientHandling import Client
from datetime import datetime, timedelta
import FastLogger as logger

ClientCount = 0
ClientList = []

app = FastAPI()

# Deifne root path
@app.get("/")
def read_root():
    """
    Handles GET requests to the root URL.
    """
    return {"ClientCount": Client.GetClientCount()}

# Define path for getting new links
@app.get("/new_link")
def readItem():
    """
    Handles GET requests to retrieve a new link.
    return str: link
    """
    url = DB.getUncheckedURL()
    if url != None:
        response = {'url': url}
        return response
    return

@app.post("/update")
def updateLinks(payload: dict):
    """
    Handles POST requests to update links.
    payload: dict containing 'url', 'page', 'old_url', and 'Client'
    return list: updated links
    """
    try:
        # Unpack payload
        new_url = payload.get('url')
        new_page = payload.get('page')
        old_url = payload.get('old_url')
        client_id = payload.get('Client')

        # Handle client heartbeat
        client = Client.GetClient(client_id)
        if client_id is None:
            logger.loggingWarning(f"Client {client_id} doesn't exsist!")
            return {"error": "Client ID is missing"}
        else:
            client.UpdateHeartbeat()

        # Update links in the database
        updated_links = DB.batchAddWebsites(new_url, new_page, old_url, client_id)
        return updated_links
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/update_checked_urls")
def updateCheckedUrls(payload: dict):
    """
    Handles POST requests to update checked URLs.
    payload: dict containing 'checked_urls'
    """
    try:
        checked_urls = payload.get('checked_urls')
        DB.updateCheckedStatus(checked_urls)
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}

@app.get('/new_client')
def newClient(request: Request):
    """
    Handles GET requests to register a new client.
    return int: client ID
    """
    # Register new client
    client_ip = request.client.host
    new_client = Client(datetime.now(), client_ip)
    ClientList.append(new_client)
    client_id = new_client.ClientNumber
    logger.loggingInfo(f"New client connected: {client_id} from IP: {client_ip}")
    return {"ClientID": client_id}
