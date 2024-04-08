from flask import Flask, render_template, request, jsonify
import requests
import DB
import locale
import time
import logging


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

locale.setlocale(locale.LC_ALL, '')

app = Flask(__name__)

url_entries = ""

def process_entries(entries_string):
    global url_entries
    entries_string = entries_string.replace("[", "").replace("]", "").replace("'", "")
    entry_strings = entries_string.split("}, {")
    entries_string = entries_string.replace("url:", "").replace("{", "").replace("}", "")
    #print(entries_string)
    url_entries = str(entries_string)
    
@app.route('/')
def index():
    my_variable = "Hello, Flask!"

    total_records = 1000
    Unsearched = 2000
    Searched = 3000

    return render_template('index.html', total_records=total_records, Unsearched=Unsearched, Searched=Searched)

@app.route('/update_content')
def update_content():
    total_records_Unformatted = int(DB.get_sites_count())
    Searched_Unformatted = int(DB.get_sites_checked())
    total_records = locale.format_string("%d", total_records_Unformatted, grouping=True)
    Searched = locale.format_string("%d", Searched_Unformatted, grouping=True)
    Unsearched_Unformatted = total_records_Unformatted - Searched_Unformatted
    Unsearched = locale.format_string("%d", Unsearched_Unformatted, grouping=True)
    Percent = round(Searched_Unformatted / total_records_Unformatted * 100, 2) 

    url = "http://localhost:5000/entries"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        process_entries(str(data))
        #print(data)
    else:
        print(f"Error: {response.status_code}")



    return jsonify({
        'total_records': total_records,
        'Unsearched': Unsearched,
        'Searched': Searched,
        'Percent': str(Percent) + "%",
        'Sites': url_entries,
    })

if __name__ == '__main__':
    url = "http://localhost:5000/entries"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        process_entries(str(data))
        #print(data)
    else:
        print(f"Error: {response.status_code}")
    app.run(host='0.0.0.0', port=8000, debug=True)
