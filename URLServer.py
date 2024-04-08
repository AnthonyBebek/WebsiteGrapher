import logging
import DB
from flask import Flask, jsonify, request, render_template
from colorama import init, Fore, Style
import datetime
init()
ClientCount = 0

ServerInfo = F"{Fore.WHITE}[{Fore.MAGENTA}Server Info{Fore.WHITE}]{Fore.MAGENTA}"

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

Current_Urls = []

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
    data = request.get_json()
    url = data.get('url', '')
    old_url = data.get('old_url', '')
    client_id = data.get('Client', '')

    Current_Urls.insert(0, url)

    if len(Current_Urls) > 14:
        Current_Urls.pop()

    output, output2 = DB.insert_into_sites(old_url, url, client_id)
    url_manager.add_entry(output2, client_id)

    return output

@app.route('/update_checked_urls', methods=['POST'])
def update_checked_urls_route():
    data = request.json
    global checked_urls
    checked_urls = data.get('checked_urls', [])
    DB.update_checked_status(data.get('checked_urls', []))

    return "Ok"

@app.route('/newclient', methods=['GET'])
def newclient():
    global ClientCount
    ClientCount = ClientCount + 1
    print(f"{ServerInfo} New Client Registered {ClientCount}")
    response = {'Client': str(ClientCount)}
    return jsonify(response)

@app.route('/disconnect', methods=['POST'])
def disconnect():
    data = request.json
    Disconnect_ID = data.get('ID', [])
    Disconnect_Url = data.get('URL', [])
    #DB.update_checked_status(data.get('checked_urls', []))
    print(f"{ServerInfo} Client {Fore.CYAN}{Disconnect_ID}{Fore.MAGENTA} disconnected, rechecking {Fore.WHITE}{Disconnect_Url}")
    return "Ok"

@app.route('/entries', methods=['GET'])
def entries():
    return jsonify(url_manager.url_array)

@app.route('/stats')
def stats():
    total_records = DB.get_sites_count()
    Unsearched = DB.get_sites_checked()
    Searched = int(total_records) - int(Unsearched)

    return render_template('stats.html')
    
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



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=27016)
