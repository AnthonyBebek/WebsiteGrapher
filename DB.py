'''
This script is used as a dependancy for the URLServer.py file, if you are running this program as a client only, then it's safe to delete it

This script stores the URLs in a DB and gets a new link
'''

import mysql.connector
import mysql.connector.pooling
from colorama import init, Fore, Style
import random
from db_config import db_config
import sys
import logger
import time
init()

errorcode = F"{Fore.WHITE}[{Fore.RED}!{Fore.WHITE}]{Fore.RED}"
addcode = F"{Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}]{Fore.GREEN}"
checkcode = F"{Fore.WHITE}[{Fore.YELLOW}~{Fore.WHITE}]{Fore.YELLOW}"
foundcheck = F"{Fore.WHITE}[{Fore.MAGENTA}~{Fore.WHITE}]{Fore.MAGENTA}"
IDCodeOpen = F"{Fore.WHITE}[{Fore.CYAN}"
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


    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    try:
        get_curreny_websites_query = "SELECT COUNT(*) FROM sites UNION SELECT COUNT(*) FROM sites WHERE checked = 1;"
        cursor.execute(get_curreny_websites_query)
        count_result = cursor.fetchall()
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
        cursor.execute(update_stats_query)
        connection.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        connection.close()
        cursor.close()

def get_server_stats():
    '''
    Returns;

    - Websites Logged Count
    - Websites Searched Count
    - Currently Connected Clients
    - Current Time

    from the stats table in the database

    '''

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    try:
        get_server_stats_query = "SELECT WebLogged, WebSearch, Clients, DATETIME FROM stats ORDER BY ID DESC LIMIT 12;"
        cursor.execute(get_server_stats_query)
        stats_result = cursor.fetchall()
        #print(stats_result)
        Web_Logged_Count = []
        Web_Searched_Count = []
        Connected_Clients = []
        timestamp = []
        if stats_result:
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

get_server_stats()
    

def insert_into_sites(linkurl, url, clientid):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    try:
        get_id_query = "SELECT ID FROM sites WHERE URL = %s"
        cursor.execute(get_id_query, (linkurl,))
        link_id_result = cursor.fetchone()
        if link_id_result:
            link_id = link_id_result[0]
        else:
            link_id = None

        check_query = "SELECT COUNT(*) FROM sites WHERE URL = %s"
        cursor.execute(check_query, (url,))
        count = cursor.fetchone()[0]

        if count > 0:
            update_query = "UPDATE sites SET Ref = Ref + 1, links = CONCAT(COALESCE(links, ''), %s) WHERE URL = %s"
            update_data = (f',{link_id}' if link_id else '', url)

            cursor.execute(update_query, update_data)
            #print(update_query, update_data)
            connection.commit()
            #print(f"{checkcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.YELLOW} URL Found: {url}")
            logger.loggingDebug(f"URL Found: {url}")
            return f"{checkcode}{IDCodeOpen}{clientid}{IDCodeClose}{Fore.YELLOW} URL Found: {url}", "0-" + url
        else:
            insert_query = "INSERT INTO sites (URL, links) VALUES (%s, %s)"
            insert_data = (url, str(link_id) if link_id else None)

            cursor.execute(insert_query, insert_data)
            connection.commit()
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
    finally:
        connection.close()
        cursor.close()


def update_checked_status(url):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    update_query = "UPDATE sites SET checked = 1 WHERE url = %s"

    try:
        cursor.execute(update_query, (url,))
        connection.commit()

        #print(f"Checked status updated for URL: {url}")

    except mysql.connector.Error as err:
        logger.loggingError(f"Error: {err}")
        #print(f"Error: {err}")

    finally:
        connection.close()
        cursor.close()

def get_unchecked_url():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    try:
        select_query = "SELECT URL FROM sites WHERE checked = 0 ORDER BY RAND() LIMIT 1"
        cursor.execute(select_query)
        result = cursor.fetchone()

        if result:
            unchecked_url = result[0]
            logger.loggingDebug(f"Unchecked URL found: {unchecked_url}")
            #print(f"{foundcheck} Unchecked URL found: {unchecked_url}")
        else:
            logger.loggingError(f"No unchecked URLs found.")
            #print(f"{Fore.RED}No unchecked URLs found.")

        update_checked_status(result[0])
        connection.commit()
        return result[0] if result else None

    finally:
        connection.close()
        cursor.close()

def get_sites_count():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    count_query = "SELECT COUNT(*) FROM sites"
    cursor.execute(count_query)
    result = cursor.fetchone()
    
    if result:
        records_count = result[0]
    else:
        logger.loggingError(f"Unable to retrieve records count.")
        #print(f"{Fore.RED}Unable to retrieve records count.")

    cursor.close()
    connection.close()
    return str(records_count) if result else None


def get_sites_checked():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    count_query = "SELECT COUNT(*) FROM sites WHERE checked = 0;"
    cursor.execute(count_query)
    result = cursor.fetchone()
    
    if result:
        checked = result[0]
    else:
        logger.loggingError(f"Unable to retrieve records count.")
        #print(f"{Fore.RED}Unable to retrieve records count.")

    cursor.close()
    connection.close()
    return str(checked) if result else None

def get_data(linkurl):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    get_id_query = "SELECT ID FROM sites WHERE URL = %s"
    cursor.execute(get_id_query, (linkurl,))
    link_id_result = cursor.fetchone()
    if link_id_result:
        link_id = link_id_result[0]
    else:
        logger.loggingError(f"URL not found in the database.")
        #print("URL not found in the database.")
        return None

    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_links;")
    cursor.execute("CREATE TEMPORARY TABLE temp_links (link_id INT);")

    cursor.execute(f"CALL splitString((SELECT links FROM sites WHERE ID = {link_id}));", multi=True)

    cursor.execute("""
        SELECT URL
        FROM sites
        WHERE ID IN (
            SELECT link_id
            FROM temp_links
        );
    """)

    result = cursor.fetchall()

    cursor.execute("DROP TEMPORARY TABLE IF EXISTS temp_links;")

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




def get_data_simple():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    count_query = "SELECT ID, URL, Links FROM sites LIMIT 50"
    cursor.execute(count_query)
    result = cursor.fetchall()
    
    return result


# --------------- Example usage -----------------

#update_checked_status("https://example.com")
#insert_into_sites("https://example.com")
