import requests
from urllib.parse import urlparse, urljoin
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError, MaxRetryError
from requests.exceptions import Timeout, ConnectionError, RequestException
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colorama import init, Fore, Style
init()

addcode = F"{Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}]"
errorcode = F"{Fore.WHITE}[{Fore.RED}!{Fore.WHITE}]{Fore.RED}"
checkcode = F"{Fore.WHITE}[{Fore.YELLOW}~{Fore.WHITE}]{Fore.YELLOW}"

BeginURL = "https://explodingtopics.com/blog/most-visited-websites"

ServerIP = "http://127.0.0.1:27016"

def get_links(url, timeout=5):

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        links = list({urlparse(urljoin(url, a['href'])).scheme + '://' + '.'.join(urlparse(urljoin(url, a['href'])).netloc.split('.')[-2:]) for a in soup.find_all('a', href=True) if url not in urljoin(url, a['href'])})
        return links

    except Timeout as e:
        print(F"{errorcode} Timed Out, skipping!")
        return []
    except ConnectTimeoutError as e:
        print(F"{errorcode} Connection Timed Out, skipping!")
        return []
    except NewConnectionError as e:
        print(F"{errorcode} New Connection Error, skipping!")
        return []
    except MaxRetryError as e:
        print(F"{errorcode} Max Retry Error, skipping!")
        return []
    except ConnectionError as e:
        print(F"{errorcode} Connection Error, skipping!")
        return []
    except RequestException as e:
        print(F"{errorcode} Error: {e}")
        return []
    except:
        print(F"{errorcode} Unknown Error, Skipping!")

def get_current_url():
    server_url = ServerIP + "/query"
    try:
        response = requests.get(server_url)
        if response.status_code == 200:
            data = response.json()
            return data.get('url', 'No URL found')
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def update_url(new_url):
    server_url =  ServerIP + "/update"
    payload = {'url': new_url}
    try:
        response = requests.post(server_url, json=payload)
        if response.status_code == 200:
            print(response.text)
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def update_checked_urls(checked_urls):
    server_url =  ServerIP + "/update_checked_urls"
    payload = {'checked_urls': checked_urls}
    try:
        response = requests.post(server_url, json=payload)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    links = get_links(BeginURL)
    update_url(BeginURL)
    update_checked_urls(BeginURL)

    for i in links:
        update_url(i)

    while True:
        url = get_current_url()
        links = get_links(url)
        update_url(url)
        update_checked_urls(url)
        for i in links:
            update_url(i)

if __name__ == "__main__":
    current_url = get_current_url()
    print(f"Current URL: {current_url}")
    new_url = "https://neewexamplwwe.com"
    update_url(new_url)
    updated_url = get_current_url()
    main()
