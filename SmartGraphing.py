import networkx as nx
import matplotlib.pyplot as plt
import DB

input_url = input("Enter a URL to start from: ").strip().lower()

rows = DB.get_data(input_url)

if len(rows) > 50:
    print()
    result = str(input("There are " + str(len(rows)) + " found websites linked to this website, do you want to limit to the first 50 or continue? (Y/N (Default)): ")).upper()
    print()
    if result == "Y":
        rows = rows[:51]
    
rows.insert(0, (input_url,)) 


G = nx.Graph()

for row in rows:
    G.add_node(row[0].strip().lower())
if input_url:
    for row in rows:
        if row[0] != input_url:
            G.add_edge(input_url, row[0].strip().lower())

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_size=50)
plt.show()
