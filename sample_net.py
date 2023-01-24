import networkx as nx
import numpy as np
import matplotlib.pyplot as plt


#G = nx.scale_free_graph(n=1000)
G = nx.barabasi_albert_graph(n=1000, m=12)

degree_sequence = sorted((d for n, d in G.degree()), reverse=True)
dmax = max(degree_sequence)
fig = plt.figure("Degree of a BA graph", figsize=(8, 8))
# Create a gridspec for adding subplots of different sizes
axgrid = fig.add_gridspec(5, 4)
ax0 = fig.add_subplot(axgrid[0:3, :])
H=G.to_undirected()
Gcc = H.subgraph(sorted(nx.connected_components(H), key=len, reverse=True)[0])

pos = nx.spring_layout(Gcc, seed=10396953)
nx.draw_networkx_nodes(Gcc, pos, ax=ax0, node_size=20)
nx.draw_networkx_edges(Gcc, pos, ax=ax0, alpha=0.4)
ax0.set_title("Connected components of G")
ax0.set_axis_off()
ax1 = fig.add_subplot(axgrid[3:, :2])
ax1.plot(degree_sequence, "b-", marker="o")
ax1.set_title("Degree Rank Plot")
ax1.set_ylabel("Degree")
ax1.set_xlabel("Rank")
ax2 = fig.add_subplot(axgrid[3:, 2:])
ax2.bar(*np.unique(degree_sequence, return_counts=True))
ax2.set_title("Degree histogram")
ax2.set_xlabel("Degree")
ax2.set_ylabel("# of Nodes")


ax1.set_yscale('log')
ax1.set_xscale('log')

fig.tight_layout()
plt.show()

"""
pos = nx.spring_layout(g, seed=10396953)
nx.draw_networkx_nodes(g, pos, node_size=20)
nx.draw_networkx_edges(g, pos, alpha=1)

fedges = filter(lambda x: g.degree()[x[0]] > 0 and g.degree()[x[1]] > 0, g.edges())
f = nx.Graph() 
f.add_edges_from(fedges)

pos = nx.spring_layout(f, seed=10396953)
nx.draw_networkx_nodes(f, pos, node_size=20)
nx.draw_networkx_edges(f, pos, alpha=0.4)


g = nx.expected_degree_graph(a, selfloops = False)
fedges = filter(lambda x: g.degree()[x[0]] > 0 and g.degree()[x[1]] > 0, g.edges())
f = nx.Graph() 
f.add_edges_from(fedges)
del g
g = f.to_directed()

---biedges = {(u, v) for u, v in g.edges}
---biedges = {(u, v) for u, v in f.edges}
---hide = {(u, v) for u, v in {(u, v) for u, v in g.edges}}
---hide = {(u, v) for v, u in {(u, v) for u, v in f.edges}}
biedges2 = {(u, v) for u, v in {(u, v) for u, v in g.edges}}
biedges = {(u, v) for v,u in {(u, v) for u, v in f.edges}}
hide = biedges2 - biedges
g.remove_edges_from(hide)



"""