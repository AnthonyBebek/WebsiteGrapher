from typing import Union
from fastapi import FastAPI, Request
import DB as DB
from ClientHandling import Client
from datetime import datetime, timedelta
import Logger as logger

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
        StatusCode = payload.get('StatusCode')
        DB.updateCheckedStatus(checked_urls, StatusCode)
        if StatusCode == 429:
            logger.loggingWarning(f"Received 429 Too Many Requests for URLs: {checked_urls}")
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

@app.get("/robots_txt/{site_id}")
def getRobotsTxt(site_id: int):
    '''
    % Retrieves the robots.txt rules for a given site.
    %
    Params:
        site_id: int - The ID of the site.
    Returns:
        dict: The robots.txt rules or an error message.
    '''
    try:
        robots_txt = DB.getRobotsTxt(site_id)
        if robots_txt:
            return robots_txt
        else:
            return {"error": "No robots.txt found for site."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/robots_txt")
def AddRobotsTxt(payload: dict):
    '''
    % Creates or updates the robots.txt rules for a site.
    %
    Params:
        payload: dict - Contains 'site_url', 'allowed', 'disallowed', and 'user_agent'.
    Returns:
        dict: Success or error message.
    '''
    try:
        site_url = payload.get('site_url')
        allowed = payload.get('allowed')
        disallowed = payload.get('disallowed')
        user_agent = payload.get('user_agent')
        
        DB.createRobotsTxt(site_url, allowed, disallowed, user_agent)
        return {"status": "created"}
    except Exception as e:
        return {"error": str(e)}
