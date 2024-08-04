import sqlite3
import networkx as nx
import matplotlib.pyplot as plt
import DB

DB.start_db()

rows = DB.get_data_simple()

G = nx.Graph()

for row in rows:
    G.add_node(row[1])

for row in rows:
    source_url = row[1]
    links = row[2].split(',')
    for link in links:
        link_id = link.strip()
        if link_id != '' and link_id.isdigit():
            link_id = int(link_id)
            if link_id < len(rows):
                target_url = rows[link_id][1]
                G.add_edge(source_url, target_url)

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=50)
plt.show()
