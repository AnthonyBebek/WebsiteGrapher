import mysql.connector
from db_config import db_config

#connection = mysql.connector.connect(**db_config)

def get_sites_count():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    count_query = "SELECT COUNT(*) FROM sites"
    cursor.execute(count_query)
    result = cursor.fetchone()
    
    if result:
        records_count = result[0]
    else:
        print(f"{Fore.RED}Unable to retrieve records count.")

    cursor.close()
    connection.close()
    return str(records_count) if result else None


def get_sites_checked():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    count_query = "SELECT COUNT(*) FROM sites WHERE checked = 1;"
    cursor.execute(count_query)
    result = cursor.fetchone()
    
    if result:
        checked = result[0]
    else:
        print(f"{Fore.RED}Unable to retrieve records count.")

    cursor.close()
    connection.close()
    return str(checked) if result else None
