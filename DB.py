'''
This script is used as a dependancy for the URLServer.py file, if you are running this program as a client only, then it's safe to delete it

This script stores the URLs in a DB and gets a new link
'''

import mysql.connector
import mysql.connector.pooling
from colorama import init, Fore, Style
from typing import List, Tuple
import random
import sys
import logger
import time
import sqlite3
import os
import json

init()

SuppressWarnings = False


def connect_to_db() -> str:
    """
    Establishes connection to database given settings in config.json

    Returns: 
        Database Type
        Database Configuration
    """
    if not os.path.exists('./config.json'):
        logger.loggingError("Config file not found!")
        exit()
    else:
        configData = json.load(open("./config.json"))
        databaseConfig = configData["Database"]
        DBType = databaseConfig[0]['Type']
        if DBType == "MySQL":
            DBType = 'mysql'
            logger.loggingInfo("Using external MYSQL Server")
        else:
            DBType = 'sqlite'
            sqlite_file = "websites.sqlite"
            logger.loggingInfo("Using SQLite DB")
            if not os.path.exists(sqlite_file):
                logger.loggingWarning("SQLite file not found, creating new database")
                open(sqlite_file, 'w').close()
            DBConfig = {'db_file': sqlite_file}
            if SuppressWarnings == False:
                logger.loggingWarning('Using SQLite as DB, this is not recommended for servers with more than 10,000 sites')
            else:
                print("Ok")
        return DBType, DBConfig

def create_tables_if_not_exist(connection):
    create_sites_table = """
    CREATE TABLE IF NOT EXISTS sites (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        Ref INTEGER DEFAULT 1,
        Links TEXT DEFAULT '0',
        Checked INTEGER DEFAULT 0,
        URL TEXT NOT NULL
    );
    """
    create_stats_table = """
    CREATE TABLE IF NOT EXISTS stats (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        WebLogged INTEGER DEFAULT 0,
        WebSearch INTEGER DEFAULT 0,
        Clients INTEGER DEFAULT 0,
        Datetime DATETIME DEFAULT NULL
    );
    """
    insert_first_website = """
    INSERT INTO sites (URL)
    VALUES ('https://explodingtopics.com/blog/most-visited-websites');
    """
    cursor = connection.cursor()
    cursor.execute(create_sites_table)
    cursor.execute(create_stats_table)
    cursor.execute(insert_first_website)
    connection.commit()

def connect(DBType, DBConfig):
    if DBType == 'mysql':
        connection = mysql.connector.connect(
        host=DBConfig['host'],
        user=DBConfig['user'],
        password=DBConfig['password'],
        database=DBConfig['websites']
    )  
    elif DBType == "sqlite":
        connection = sqlite3.connect(DBConfig['db_file'], check_same_thread=False)
        create_tables_if_not_exist(connection)
    else:
        logger.loggingError("Unsupported database type!")
        quit()
    return connection

def execute_query(connection, query: str, params: str = None, commit: bool = False, many: bool = False):

    if DBType == 'sqlite':
        if 'CONCAT' in query:
            while 'CONCAT' in query:
                start = query.index('CONCAT')
                end = query.index(')', start) + 1
                concat_part = query[start:end]
                concat_replacement = concat_part.replace('CONCAT(', '').replace(')', '').replace(', ', ' || ')
                query = query[:start] + concat_replacement + query[end:]

        query = query.replace('%s', '?')
        query = query.replace('CURTIME()', "time('now')")
        query = query.replace('CURRENT_TIMESTAMP', "datetime('now')")
        query = query.replace('RAND()', "RANDOM()")

    cursor = connection.cursor()
    if many:
        cursor.executemany(query, params or ())
    else:
        cursor.execute(query, params or ())
    if commit:
        connection.commit()
    return cursor

def fetchall(cursor):
    return cursor.fetchall()

def fetchone(cursor):
    return cursor.fetchone()

def close_connection(connection):
    connection.close()

DBType, DBConfig, connection = None, None, None

def start_db():
    global connection
    global DBType
    global DBConfig
    DBType, DBConfig = connect_to_db()
    connection = connect(DBType, DBConfig)

    return connection

errorcode = F"{Fore.WHITE}[{Fore.RED}!{Fore.WHITE}]{Fore.RED}"
addcode = F"{Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}]{Fore.GREEN}"
checkcode = F"{Fore.WHITE}[{Fore.YELLOW}~{Fore.WHITE}]{Fore.YELLOW}"
foundcheck = F"{Fore.WHITE}[{Fore.MAGENTA}Server Info{Fore.WHITE}]{Fore.MAGENTA}"
IDCodeOpen = F"{Fore.WHITE}[{Fore.CYAN}Client: "
IDCodeClose = F"{Fore.WHITE}]"

def update_server_stats(Clients):


    '''
    Adds a new entry to the stats table.

    Inserts;

    - Websites Logged Count
    - Websites Searched Count
    - Currently Connected Clients
    - Current Time
    
    '''

    # Get the current Websites Logged Count


    try:
        get_curreny_websites_query = "SELECT COUNT(*) FROM sites UNION SELECT COUNT(*) FROM sites WHERE checked = 1;"
        cursor = execute_query(connection, get_curreny_websites_query)
        count_result = fetchall(cursor)
        if count_result:
            Web_Logged_Count = count_result[0][0]
            Web_Searched_Count = count_result[1][0]
        else:
            Web_Logged_Count = None
            Web_Searched_Count = None

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    try:
        update_stats_query = f"INSERT INTO stats (WebLogged, WebSearch, Clients, DATETIME) VALUES ({Web_Logged_Count}, {Web_Searched_Count}, {Clients}, CURTIME())"
        cursor = execute_query(connection, update_stats_query, commit = True)

    except mysql.connector.Error as err:
        print(f"Error: {err}")

def get_server_stats():
    '''
    Returns;

    - Websites Logged Count
    - Websites Searched Count
    - Currently Connected Clients
    - Current Time

    from the stats table in the database

    '''

    try:
        get_server_stats_query = "SELECT WebLogged, WebSearch, Clients, DATETIME FROM stats ORDER BY ID DESC LIMIT 12;"
        cursor = execute_query(connection, get_server_stats_query)
        stats_result = fetchall(cursor)
        #print(stats_result)
        Web_Logged_Count = []
        Web_Searched_Count = []
        Connected_Clients = []
        timestamp = []
        if not stats_result == None:
            for entry in stats_result:
                Web_Logged_Count.append(entry[0])
                Web_Searched_Count.append(entry[1])
                Connected_Clients.append(entry[2])
                timestamp.append(entry[3])
        else:
            Web_Logged_Count = None
            Web_Searched_Count = None
            Connected_Clients = None
            timestamp = None

        Web_Logged_Count.reverse()
        Web_Searched_Count.reverse()
        Connected_Clients.reverse()
        timestamp.reverse()

        Fixed_Timestamps = []

        for time in timestamp:
            time = str(time)
            time.replace("datetime.datetime", "")
            time = time[11:]
            time = time[:-3]
            Fixed_Timestamps.append(time)
        Fixed_Timestamps = list(Fixed_Timestamps)

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    return Web_Logged_Count, Web_Searched_Count, Connected_Clients, Fixed_Timestamps 
    

def insert_into_sites(linkurl: str, urls: list, clientid: str) -> None:

    try:
        get_id_query = "SELECT ID FROM sites WHERE URL = %s"
        cursor = execute_query(connection, get_id_query, (linkurl,))
        link_id_result = fetchall(cursor)
        if link_id_result:
            link_id = link_id_result[0]
        else:
            link_id = None

        check_query = "SELECT COUNT(*) FROM sites WHERE URL = %s"
        cursor = execute_query(connection, check_query, (url,))
        count = fetchone(cursor)[0]

        if count > 0:
            update_query = "UPDATE sites SET Ref = Ref + 1, links = CONCAT(COALESCE(links, ''), %s) WHERE URL = %s"
            update_data = (f',{link_id}' if link_id else '', url)

            cursor = execute_query(connection, update_query, update_data, commit=True)
            #print(update_query, update_data)
            #print(f"{checkcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.YELLOW} URL Found: {url}")
            logger.loggingDebug(f"URL Found: {url}")
            return f"{checkcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.YELLOW} URL Found: {url}", "0-" + url
        else:
            insert_query = "INSERT INTO sites (URL, links) VALUES (%s, %s)"
            insert_data = (url, str(link_id) if link_id else None)

            cursor = execute_query(connection, insert_query, insert_data, commit=True)
            #print(f"{addcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.GREEN} Added: {url}")
            logger.loggingDebug(f"Added: {url}")
            try:
                return f"{addcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.GREEN} Added: {url}", "1-" + url
            except:
                logger.loggingWarning(f"Missed returning message")
                return ""
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "Null", "Null"


def update_checked_status(url):
    update_query = "UPDATE sites SET checked = 1 WHERE url = %s"

    try:
        execute_query(connection, update_query, (url,), commit=True)

        #print(f"Checked status updated for URL: {url}")

    except mysql.connector.Error as err:
        logger.loggingError(f"Error: {err}")
        #print(f"Error: {err}")

def get_unchecked_url():

    try:
        select_query = "SELECT URL FROM sites WHERE checked = 0 ORDER BY RAND() LIMIT 1"
        cursor = execute_query(connection, select_query)
        result = fetchone(cursor)

        if result:
            unchecked_url = result[0]
            logger.loggingDebug(f"Unchecked URL found: {unchecked_url}")
            #print(f"{foundcheck} Unchecked URL found: {unchecked_url}")
        else:
            logger.loggingError(f"No unchecked URLs found.")
            #print(f"{Fore.RED}No unchecked URLs found.")

        update_checked_status(result[0])
        return result[0] if result else None
    
    except:
        logger.loggingError("Error found in get_unchecked_url()")

def get_sites_count():

    count_query = "SELECT COUNT(*) FROM sites"
    cursor = execute_query(connection, count_query)
    result = fetchone(cursor)
    
    if result:
        records_count = result[0]
    else:
        logger.loggingError(f"Unable to retrieve records count.")
        #print(f"{Fore.RED}Unable to retrieve records count.")

    return str(records_count) if result else None


def get_sites_checked():

    count_query = "SELECT COUNT(*) FROM sites WHERE checked = 0;"
    cursor = execute_query(connection, count_query)
    result = fetchone(cursor)
    
    if result:
        checked = result[0]
    else:
        logger.loggingError(f"Unable to retrieve records count.")
        #print(f"{Fore.RED}Unable to retrieve records count.")

    return str(checked) if result else None

def split_string(connection, link_id):
    select_query = "SELECT links FROM sites WHERE ID = ?"
    cursor = execute_query(connection, select_query, (link_id,))
    result = fetchone(cursor)

    if result:
        links = result[0]
        link_ids = links.split(',')
        return [int(link_id) for link_id in link_ids if link_id.isdigit()]
    return []

def get_data(linkurl):
    get_id_query = "SELECT ID FROM sites WHERE URL = ?"
    cursor = execute_query(connection, get_id_query, (linkurl,))
    link_id_result = fetchone(cursor)
    if link_id_result:
        link_id = link_id_result[0]
    else:
        logger.error(f"URL not found in the database.")
        return None

    execute_query(connection, "DROP TABLE IF EXISTS temp_links;", commit=True)
    execute_query(connection, "CREATE TABLE temp_links (link_id INTEGER);", commit=True)

    # Simulate CALL splitString
    link_ids = split_string(connection, link_id)
    insert_query = "INSERT INTO temp_links (link_id) VALUES (?);"
    for lid in link_ids:
        execute_query(connection, insert_query, (lid,), commit=True)

    result_cursor = execute_query(connection, """
        SELECT URL
        FROM sites
        WHERE ID IN (
            SELECT link_id
            FROM temp_links
        );
    """)
    result = fetchall(result_cursor)

    execute_query(connection, "DROP TABLE IF EXISTS temp_links;", commit=True)
    return result


# TODO - Add Procedure to script, or add this manually to make this work again

'''
DROP PROCEDURE IF EXISTS splitString;

DELIMITER $$

CREATE PROCEDURE splitString(input VARCHAR(16384))
BEGIN
    DECLARE delim VARCHAR(1) DEFAULT ',';
    DECLARE position INT;
    DECLARE piece VARCHAR(255);  -- Declare piece variable outside the loop
    SET position = 1;
    SET input = CONCAT(input, delim);

    -- Initialize piece variable
    SET piece = SUBSTRING(input, position, LOCATE(delim, input, position) - position);

    WHILE LOCATE(delim, input, position) > 0 DO
        SET piece = SUBSTRING(input, position, LOCATE(delim, input, position) - position);
        INSERT INTO temp_links (link_id) VALUES (CAST(piece AS INT));  -- Insert values directly into the temp_links table
        SET position = LOCATE(delim, input, position) + 1;
    END WHILE;
END$$

DELIMITER ;
'''


def batchUpdateUrl(connection, urls: List[str], link_id: str, clientid: str) -> List[Tuple[str, str]]:
    check_query = "SELECT URL FROM sites WHERE URL IN (%s)" % ','.join(['%s'] * len(urls))
    urls = list(urls)
    time.sleep(2)
    cursor = execute_query(connection, check_query, tuple(urls))
    existing_urls = set(row[0] for row in cursor.fetchall())  # URLs that already exist in the DB

    # Prepare data for batch processing
    update_data = []
    insert_data = []
    results = []

    for url in urls:
        if url in existing_urls:
            # Prepare data for updating
            update_data.append((f',{link_id}' if link_id else '', url))
            results.append((f"{checkcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.YELLOW} URL Found: {url}", "0-" + url))
        else:
            # Prepare data for inserting
            insert_data.append((url, str(link_id) if link_id else None))
            results.append((f"{addcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.GREEN} Added: {url}", "1-" + url))

    # Execute batch updates
    if update_data:
        update_query = """
            UPDATE sites
            SET Ref = Ref + 1, links = CONCAT(COALESCE(links, ''), %s)
            WHERE URL = %s
        """
        execute_query(connection, update_query, update_data, commit=True, many=True)

    # Execute batch inserts
    if insert_data:
        insert_query = "INSERT INTO sites (URL, links) VALUES (%s, %s)"
        execute_query(connection, insert_query, insert_data, commit=True, many=True)

    return results



def get_data_simple():

    count_query = "SELECT ID, URL, Links FROM sites LIMIT 50"
    cursor = execute_query(connection, count_query)
    result = fetchall(cursor)
    
    return result

if __name__ == '__main__':
    print()
    print("-----------------------------------")
    print("Hey! Run URLServer.py not this file")
    print("-----------------------------------")
