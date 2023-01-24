import matplotlib.pyplot as plt


density = []
num_nodes = []
proc_time = []
sim_time = []
with open('mylog.log', 'r') as h:
    line = h.readline()
    while line:
        if line.startswith("INFO:root:Graph Size:"):
            line.strip()
            num_nodes.append(int(line.rsplit(":", 1)[1]))
        elif line.startswith("INFO:root:SUB-Graph density"):
            line.strip()
            density.append(float(line.rsplit(":",1)[1]))
        elif line.startswith("INFO:root:_____________Running time:"):
            proc_time.append(float(line.rsplit(" ")[2]))
        elif line.startswith("INFO:root:______________Hourly Stats a"):
            sim_time.append(float(line.rsplit(" ")[-2]))
        line = h.readline()


plt.scatter(num_nodes, density)
plt.ylim(0, max(density)+max(density)*0.10)
plt.show()


plt.plot(num_nodes)
plt.ylim(0, max(num_nodes))
plt.title("Num Nodes")
plt.show()


plt.plot(density)
plt.ylim(0, max(density)+max(density)*0.10)
plt.title("Density")
plt.show()

plt.scatter(sim_time, proc_time)
#plt.ylim(0, max(density)+max(density)*0.10)
plt.title("Proc Time")
plt.show()
