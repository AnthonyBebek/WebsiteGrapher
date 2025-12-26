import requests
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tldextract
from requests.exceptions import Timeout, RequestException
from colorama import init, Fore
from urllib3.exceptions import NewConnectionError, ConnectTimeoutError, MaxRetryError
import time
import signal
import threading

addcode = F"{Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}]"
errorcode = F"{Fore.WHITE}[{Fore.RED}!{Fore.WHITE}]{Fore.RED}"
failcode = F"{Fore.WHITE}[{Fore.CYAN}-{Fore.WHITE}]{Fore.CYAN}"
checkcode = F"{Fore.WHITE}[{Fore.YELLOW}~{Fore.WHITE}]{Fore.YELLOW}"
newurl = F"{Fore.WHITE}[{Fore.MAGENTA}~{Fore.WHITE}]{Fore.MAGENTA}"


id = 0

ServerIP = "http://127.0.0.1:8000"

# Create a session for connection pooling
session = requests.Session()

def registerClient() -> str:
    server_url = ServerIP + "/new_client"
    while True:
        try:
            print(f"Asking {server_url} for new client ID")
            response = requests.get(server_url)
            if response.status_code == 200:
                data = response.json()
                return data.get('ClientID', '')
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error: {e}")

def getLinks(url) -> tuple:
    '''
    Gets all links from a given URL.
    
    Params:
        url: str - The URL to fetch links from.
    Returns:
        tuple: (list of links, page content in base64)
    '''
    try:
        start_time = time.time()
        # Use session for connection pooling
        response = session.get(url, timeout=4)
        response.raise_for_status()

        # Use lxml parser for faster HTML parsing
        soup = BeautifulSoup(response.text, 'lxml')

        # Extract all unique links from the page
        links = {
            urljoin(url, a['href'])
            for a in soup.find_all('a', href=True)
            if a['href'].startswith(('http://', 'https://')) and url not in a['href']
        }

        # Only extract top-level domains
        links = {
            urlparse(link).scheme + '://' + tldextract.extract(link).registered_domain
            for link in links
        }

        # Encode the page to base64 to prevent excape character issues
        page = base64.b64encode(soup.get_text().encode('utf-8')).decode('utf-8')

        end_time = time.time()
        # Print fetch and parse time for debugging
        print(f"{checkcode} Fetched and parsed {url} in {end_time - start_time:.2f} seconds")
        return list(links), page

    except Timeout:
        print(f"{failcode} Timed Out, skipping!")
        return []
    except ConnectTimeoutError:
        print(f"{failcode} Connection Timed Out, skipping!")
        return []
    except NewConnectionError:
        print(f"{failcode} New Connection Error, skipping!")
        return []
    except MaxRetryError:
        print(f"{failcode} Max Retry Error, skipping!")
        return []
    except ConnectionError:
        print(f"{failcode} Connection Error, skipping!")
        return []
    except RequestException as e:
        print(f"{errorcode} Error: {e}")
        return []
    except KeyboardInterrupt:
        print(f"{checkcode} Exiting")
        exit()
    except Exception as e:
        print(f"{errorcode} Unknown Error: {e}, Skipping!")
        return []

def getCurrentURL() -> str: 
    '''
    Retrieves the current URL to be processed from the server.
    Returns:
        str: The URL to process or None if an error occurs.
    '''
    server_url = ServerIP + "/new_link"
    try:
        response = requests.get(server_url)
        if response.status_code == 200:
            data = response.json()
            return data.get('url', 'No URL found')
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except:
        return None
    
def updateLinks(new_url, new_page, old_url) -> list:
    '''
    Updates the links on the server with new information.
    
    Params:
        new_url: str - The new URLS found from old_url.
        new_page: str - The content of the old_url page in base64.
        old_url: str - The old URL.
    Returns:
        list: The server's response data or an empty list if an error occurs.
    '''
    server_url = ServerIP + "/update"
    payload = {
        'url': new_url,
        'page': new_page,
        'old_url': old_url,
        'Client': id
    }
    try:
        response = requests.post(server_url, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
    except:
        return []

def updateCheckedUrls(checked_urls) -> None:
    '''
    Updates the checked URLs on the server.
    Params:
        checked_urls: list - List of URLs that have been checked.
    Returns:
        None
    ''' 
    server_url = ServerIP + "/update_checked_urls"
    payload = {
        'checked_urls': checked_urls
    }
    try:
        response = requests.post(server_url, json=payload)
        if response.status_code == 200:
            return
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return
    except:
        return
    
def disconnect(id, url) -> None:
    '''
    Disconnects the client from the server.
    Params:
        id: str - The client ID.
        url: str - The URL being processed (if any).
    Returns:
        None
    '''
    server_url = ServerIP + "/disconnect"
    payload = {
        'ID': id,
        'URL': url
    }
    try:
        response = requests.post(server_url, json=payload)
        if response.status_code == 200:
            return
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return
    except:
        return

def main():
    global id
    print("Registering Client...")
    id = registerClient()
    if id == None:
        print(f"{errorcode} Failed to register client!")
        print(f"{checkcode} Have you changed the Server IP?{Fore.WHITE} - {Fore.CYAN}{ServerIP}")
        print()
        print(f"{errorcode} Quitting{Fore.WHITE}")
        exit()

    print(f"Received Client ID: {id}")
    # Use an event to allow the sleep to be interruptible
    stop_event = threading.Event()

    # Signal handler to set the stop event
    def _signal_handler(signum, frame):
        print(f"{checkcode} Signal received ({signum}), shutting down...")
        stop_event.set()

    # Register for SIGINT (Ctrl+C) and SIGTERM
    signal.signal(signal.SIGINT, _signal_handler)
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
    except AttributeError:
        # SIGTERM may not exist on some platforms (Windows)
        pass

    try:
        while not stop_event.is_set():
            current_url = getCurrentURL()
            if current_url == None:
                # wait a short while but wake if stop_event set
                stop_event.wait(0.1)
                continue

            print(f"{newurl} Fetched URL: {current_url}")
            try:
                new_urls, page = getLinks(current_url)
            except Exception as e:
                print(f"{errorcode} Error fetching links from {current_url}: {e}")
                updateCheckedUrls([current_url])
                continue

            if not new_urls:
                # getLinks prints errors; wait then continue
                stop_event.wait(1)
                print(f"{failcode} No links found on {current_url}, skipping!")
                updateCheckedUrls([current_url])
                continue

            print(f"{addcode} Found {len(new_urls)} links on {current_url}")
            updated_links = updateLinks(new_urls, None, current_url)
            print(f"{addcode} Updated links on server, received {len(updated_links)} new links")
            updateCheckedUrls([current_url])

    except Exception as e:
        print(f"{errorcode} Unexpected error in main loop: {e}")
    finally:
        print(f"{checkcode} Sending disconnect packet")
        try:
            disconnect(id, None)
        except Exception:
            pass

if __name__ == "__main__":
    init()
    main()