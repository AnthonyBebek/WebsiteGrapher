query = "SELECT * FROM some_table"
cursor = execute_query(connection, query)
results = fetchall(cursor)


query = "INSERT INTO stats (WebLogged, WebSearch, Clients, DATETIME) VALUES (%s, %s, %s, CURTIME())"
params = (Web_Logged_Count, Web_Searched_Count, Clients)
execute_query(connection, query, params=params, commit=True)


update_query = "UPDATE sites SET Ref = Ref + 1, links = CONCAT(COALESCE(links, ''), %s) WHERE URL = %s"
update_data = (f',{link_id}' if link_id else '', url)
execute_query(connection, update_query, update_data, commit=True)


query = "SELECT COUNT(*) FROM some_table"
cursor = execute_query(connection, query)
count = fetchone(cursor)[0]
print("Count:", count)


