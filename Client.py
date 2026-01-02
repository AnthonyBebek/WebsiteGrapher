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

ServerIP = "http://192.168.30.40:8000"

# Create a session for connection pooling
session = requests.Session()
# Tor SOCKS5h proxy (only used for getLinks requests)
TOR_SOCKS_PROXY = 'socks5h://127.0.0.1:9050'

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
        tuple: (list of links, page content in base64, status code)
    '''
    try:
        start_time = time.time()
        # Use session for connection pooling
        # Route only this request through Tor (socks5h) so DNS is resolved via Tor
        proxies = {
            'http': TOR_SOCKS_PROXY,
            'https': TOR_SOCKS_PROXY,
        }
        response = session.get(url, timeout=4, proxies=proxies)
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

        # Encode the page to base64 to prevent escape character issues
        page = base64.b64encode(soup.get_text().encode('utf-8')).decode('utf-8')

        end_time = time.time()
        # Print fetch and parse time for debugging
        print(f"{checkcode} Fetched and parsed {url} in {end_time - start_time:.2f} seconds")
        return list(links), page, response.status_code

    except Timeout:
        print(f"{failcode} Timed Out, skipping!")
        return [], None, 408
    except ConnectTimeoutError:
        print(f"{failcode} Connection Timed Out, skipping!")
        return [], None, 408
    except NewConnectionError:
        print(f"{failcode} New Connection Error, skipping!")
        return [], None, 503
    except MaxRetryError:
        print(f"{failcode} Max Retry Error, skipping!")
        return [], None, 429
    except ConnectionError:
        print(f"{failcode} Connection Error, skipping!")
        return [], None, 503
    except RequestException as e:
        print(f"{errorcode} Error: {e}")
        return [], None, response.status_code if 'response' in locals() else 500
    except KeyboardInterrupt:
        print(f"{checkcode} Exiting")
        exit()
    except Exception as e:
        print(f"{errorcode} Unknown Error: {e}, Skipping!")
        return [], None, 500

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

def updateCheckedUrls(checked_urls, exit_code) -> None:
    '''
    Updates the checked URLs on the server.
    Params:
        checked_urls: list - List of URLs that have been checked.
        exit_code: int - The exit code representing the status of the URL check.
    Returns:
        None
    ''' 
    server_url = ServerIP + "/update_checked_urls"
    payload = {
        'checked_urls': checked_urls,
        'StatusCode': exit_code
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

def fetchRobotsTxt(site_url: str):
    '''
    % Fetches the robots.txt rules for a given site from the server.
    #
    Params:
        site_url: str - The URL of the site.
    Returns:
        dict: The robots.txt rules or an error message.
    '''
    server_url = f"{ServerIP}/robots_txt/{site_url}"
    try:
        response = session.get(server_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{errorcode} Error fetching robots.txt: {response.status_code}")
            return None
    except Exception as e:
        print(f"{errorcode} Exception fetching robots.txt: {e}")
        return None

def AddRobotsTxt(site_url: str, allowed: str, disallowed: str, user_agent: str = "*") -> None:
    '''
    Creates or updates the robots.txt rules for a site on the server.
    Params:
        site_url: str - The URL of the site.
        allowed: str - Allowed paths.
        disallowed: str - Disallowed paths.
        user_agent: str - User agent the rules apply to.
    Returns:
        None
    '''
    server_url = f"{ServerIP}/robots_txt"
    payload = {
        'site_url': site_url,
        'allowed': allowed,
        'disallowed': disallowed,
        'user_agent': user_agent
    }
    try:
        response = session.post(server_url, json=payload)
        if response.status_code == 200:
            print(f"{addcode} Robots.txt created/updated successfully for site {site_url}")
        else:
            print(f"{errorcode} Error creating/updating robots.txt: {response.status_code}")
    except Exception as e:
        if 'NameResolutionError' in str(e):
            print(f"{errorcode} DNS resolution error while creating/updating robots.txt: {e}")
            stop_event.wait(10)  # Wait before continuing next
        else:
            print(f"{errorcode} Exception creating/updating robots.txt: {e}")

def fetchAndAddRobotsTxt(site_url: str, user_agent: str = "*") -> None:
    '''
    Fetches the robots.txt file for a given site, parses the allowed and disallowed paths for the specified user agent,
    and pipes the data into the API using AddRobotsTxt.

    Params:
        site_url: str - The base URL of the site (e.g., "http://example.com").
        user_agent: str - The user agent to look for in the robots.txt file.
    Returns:
        None
    '''
    robots_url = f"{site_url}/robots.txt"
    try:
        print(f"Fetching robots.txt from {robots_url}")
        response = session.get(robots_url, timeout=4)
        response.raise_for_status()

        # Parse the robots.txt content
        lines = response.text.splitlines()
        allowed = []
        disallowed = []
        current_agent = None

        for line in lines:
            line = line.strip()
            if line.startswith("User-agent:"):
                current_agent = line.split(":", 1)[1].strip()
            elif current_agent == user_agent:
                if line.startswith("Allow:"):
                    allowed.append(line.split(":", 1)[1].strip())
                elif line.startswith("Disallow:"):
                    disallowed.append(line.split(":", 1)[1].strip())

        # Join allowed and disallowed paths into strings
        allowed_str = ",".join(allowed)
        disallowed_str = ",".join(disallowed)

        # Pipe the data into the API
        AddRobotsTxt(site_url, allowed_str, disallowed_str, user_agent)

    except requests.exceptions.RequestException as e:
        print(f"{errorcode} Error fetching robots.txt: {e}")
    except Exception as e:
        print(f"{errorcode} Unknown error while processing robots.txt: {e}")

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
                result = getLinks(current_url)
                exit_code = result[2]
                if exit_code == 429: # Too many requests
                    print(f"{failcode} Received 429 Too Many Requests, waiting before retrying...")
                    stop_event.wait(10) # wait 10 seconds but wake if stop_event set
                    updateCheckedUrls([current_url], exit_code)
                    continue
                if exit_code != 200: # If status code is not 200, treat as error
                    updateCheckedUrls([current_url], exit_code)
                    continue
                else: # Successful fetch
                    new_urls, page, errorcode = result # Unpack the tuple
                    fetchAndAddRobotsTxt(current_url) # Fetch and add robots.txt rules for the site
                    updateCheckedUrls([current_url], exit_code)
            except Exception as e:
                print(f"{errorcode} Error fetching links from {current_url}: {e}")
                updateCheckedUrls([current_url], exit_code)
                continue

            if not new_urls:
                # getLinks prints errors; wait then continue
                stop_event.wait(1)
                print(f"{failcode} No links found on {current_url}, skipping!")
                updateCheckedUrls([current_url], exit_code)
                continue

            print(f"{addcode} Found {len(new_urls)} links on {current_url}")
            updated_links = updateLinks(new_urls, page, current_url)
            print(f"{addcode} Updated links on server, received {len(updated_links)} new links")
            updateCheckedUrls([current_url], exit_code)

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