# import sys
# sys.setrecursionlimit(5000)
import sys

import simpy
import random
import networkx as nx
import logging
logging.basicConfig(level=logging.INFO, filename="mylog.log")
#logging.basicConfig(level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


ONE_SECOND = 1;
ONE_MINUTE = 60 * ONE_SECOND;
ONE_HOUR = 60 * ONE_MINUTE;
ONE_DAY = 24 * ONE_HOUR;

#protocol constants:
MAX_ADDR_SEND = 200
MESSAGE_TYPES = ['ADDR', 'GETADDR']

global G
G = nx.DiGraph()

NETWORK_SIZE = 6000
# create network. according to different strategies [random (ER), scale-free (BA), realMG (from Grundmann)
def getDegreeDistribution(strategy, n, deg_seq_list=None):
    # n = NETWORK_SIZE
    if strategy == 'ba-model':
        # choose a value for m: n/100
        m = int (n / 100)
        g = nx.barabasi_albert_graph(n=n, m=m)  # m Number of edges to attach from a new node to existing nodes
    elif strategy == 'random':
        # choose a value for p: 0.05
        p = 0.05
        g = nx.fast_gnp_random_graph(n, p, seed=None, directed=False)
    elif strategy == 'scale-free':
        g = nx.scale_free_graph(n)
    elif strategy == 'deg-sequence':
        #  generate a graph according to the given degree-sequence:
        #  make sure NETWORK-SIZE is correct
        #  male sure the sequence is given
        if deg_seq_list is None:
            logging.error('Degree sequence model chosen but degree sequence given is None.')
            return []
        else:
            g =nx.expected_degree_graph(w = deg_seq_list, selfloops=False)

    else:
        logging.error(f'Unknown type of graph')
        return []

    deg_seq = sorted((d for n, d in g.degree()), reverse=True)
    return deg_seq


class BroadcastPipe(object):
    def __init__(self, env, capacity=simpy.core.Infinity):
        self.env = env
        self.capacity = capacity
        self.pipes = []

    def put(self, value):
        if not self.pipes:
            raise RuntimeError('No output pipes.')
        events = [store.put(value) for store in self.pipes]
        return self.env.all_of(events)

    def get_output_conn(self):
        pipe = simpy.FilterStore(self.env, capacity=self.capacity)
        self.pipes.append(pipe)
        return pipe

class Peer:
    def __init__(self, id, env, comm_channel):
        self.id = id
        self.online = False
        self.comm_channel = comm_channel

    def __str__(self):
        return(f"Peer_{self.id}/{self.online}")

    def send_msg(self, dest_peer, msg_type, msg_payload):
        msg = (dest_peer, msg_type, msg_payload)
        self.comm_channel.put(msg)

    def consume_message(self):
        while True:
            msg = yield self.com_channel.get(lambda msg: msg[0] == self.id)
            #process message now


class GoodPeer(Peer):
    def __init__(self, id, env, arrival_rate, departure_rate, message_rate, num_peers, in_pipe, out_pipe):
        self.id = id
        self.arrival_rate = arrival_rate # How long until coming back online after being offline
        self.departure_rate = departure_rate # How long to stay online
        self.message_rate = message_rate # How often to send an addr message
        self.type = 'GOOD' # This is a peer compliant to the protocol
        self.online = False
        self.addr_map = {} # purge every 24hours. it includes only connected peers
        self.net_connect_retries = 0
        self.num_peers = num_peers
        self.known_peers = {}  # ADDRMAN: dict of known nodes. {peer_id: timestamp} // aged nodes are removed unless connected.
        # TODO: confirm from bitcoin core
        self.max_node_age = 6 * ONE_HOUR  # chosen arbitrarilly
        self.in_pipe = in_pipe
        self.out_pipe = out_pipe

    def getPeerInfo(self):
        return f"{self.type}_Peer_{self.id}/{self.online}"

    def __repr__(self):
        return f"{self.id}"

    def startPeer(self):
        # Start the peer's message process
        self.online = True
        self.seedGETADDR()
        self.periodic_addr_generation = env.process(self.addr_gen())
        self.periodic_truncate_of_addr_map = env.process(self.truncate_addrmap())
        self.departure_process = env.process(self.departure())
        # periodically check number of connections and add if less than self.num_peers (every 30 minutes)
        self.update_connections = env.process(self.update_conns())
        self.consume_messages = env.process(self.consume_message())

    def consume_message(self):
        while True:
            msg = yield self.in_pipe.get(lambda msg_r: msg_r[0] == self.id)
            # process message now
            logging.debug(f"{self} received msg from peer_{msg[1]}: {msg[2]}. Rx-Tx{env.now - msg[4]}")
            if msg[2] == 'ADDR':
                self.receive_addr(msg[1], msg[3])

    def send_msg(self, dest_peer, msg_type, msg_payload):
        msg = (dest_peer, self.id, msg_type, msg_payload, env.now)
        self.out_pipe.put(msg)

    def update_conns(self):
        while True:
            yield env.timeout(30 * ONE_MINUTE)
            if not self.online:
                continue
            connections_diff = self.num_peers - self.get_outboundN()
            conns_count = 0
            if connections_diff > 0:
                # try to establish so many connections:
                available_peers = list(set(self.known_peers.keys()) - set(self.get_connected()))
                random.shuffle(available_peers)
                if available_peers is not None:
                    for peer_id in available_peers:
                        peer = ALL_PEERS[peer_id]
                        if peer.online:
                            G.add_edge(self.id, peer_id)
                            conns_count += 1
                        if conns_count > connections_diff:
                            break
            logging.debug(logging.debug(f"Peer_{self.id} UPDATED CONNECTIONS TO {self.get_connected()}||NUM_PEERS:{self.num_peers}"))




    def seedGETADDR(self):
        # simulate a seed look-up to bootstrap node connection
        # seed_reply = random.sample(list(G.nodes(data=False)), int(G.size()/10))
        # logging.warning(f"{int(G.number_of_nodes() / 10)} // {MAX_ADDR_SEND}")
        seed_reply = random.sample(list(G.nodes(data=False)), min(MAX_ADDR_SEND, int(G.number_of_nodes()/10)))
        for sr in seed_reply:
            self.known_peers[sr] = env.now
        #logging.debug(f"Peer_{self.id} known_peers {(self.known_peers)}")


    def truncate_addrmap(self):
        while True and len(self.addr_map) > 0:
            yield env.timeout(random.expovariate(ONE_HOUR))
            self.addr_map = {}

    def get_outbound(self):
        return list(G.successors(self.id))

    def get_outboundN(self):
        return G.out_degree[self.id]

    def get_inboundN(self):
        return G.in_degree[self.id]

    def get_inbound(self):
        return list(G.predecessors(self.id))

    def get_connected(self):
        return list(G.successors(self.id)) + list(G.predecessors(self.id))

    def update_known_addresses(self, sender_id, addrlist):
        # update known peers:
        #NET_PEERS[self.id]['known_peers'] += addrlist
        #NET_PEERS[self.id]['known_peers'] = [*set(NET_PEERS[self.id]['known_peers'])]  # Remove Duplicates
        for kp in addrlist:
            self.known_peers[kp] = env.now

        self.update_addrmap(sender_id, addrlist)

    def update_addrmap(self, sender_id, addrlist):
        # update addr_map. Key is the sender_id.
        if sender_id not in self.addr_map:
            self.addr_map[sender_id] = []
        self.addr_map[sender_id] += addrlist
        self.addr_map[sender_id] = [*set(self.addr_map[sender_id])]  # Remove Duplicates

    def addr_gen(self):
        # periodically send an addr message including 10 known peers to the connected peers, according to message rate
        while True:
            try:
                yield env.timeout(random.expovariate(1 / self.message_rate))
                if self.online:
                    # select 10 addresses:
                    #peers_list = random.sample(NET_PEERS[self.id]['known_peers'], min(10, len(NET_PEERS[self.id]['known_peers'])))
                    known_ids = list(self.known_peers.keys())
                    peers_list = random.sample( known_ids, min(10, len(known_ids)) )
                    #logging.debug(f"Peer_{self.id} sending ADDR msg with peers {peers_list}||CONNS:{self.get_connected()}")
                    # send to all connected nodes:
                    choose_fwd_peers = random.sample(self.get_connected(), min(2, len(self.get_connected())))
                    if len(peers_list) > 0:
                        for connected_peer_id in choose_fwd_peers:
                            #logging.debug(f"Peer_{self.id} sending to {connected_peer_id} ADDR msg with peers {peers_list} at {env.now}")
                            #connected_peer = ALL_PEERS[connected_peer_id]
                            # TODO send message through pipe
                            #connected_peer.receive_addr(self.id, peers_list.copy())
                            self.send_msg(connected_peer_id, 'ADDR', peers_list.copy())

                            # update addr_map
                            if connected_peer_id not in self.addr_map:
                                self.addr_map[connected_peer_id] = []
                            self.addr_map[connected_peer_id] += peers_list.copy()  # ADDR msg with peers [] a
                            self.addr_map[connected_peer_id] = [*set(self.addr_map[connected_peer_id])]

            except simpy.Interrupt as i:
                break


    def receive_message2(self, sender_id):
        # Peer receives a message from the chosen peer
        logging.debug(f"{self.type} Peer {self.id} received a message from Peer {sender_id} at time {env.now}")

    def receive_addr(self, sender_id, addrlist):
        logging.debug(f"XXX_Peer {self.id} received a addr from Peer {sender_id} with list{addrlist} at time {env.now}")
        # update known peers and addr_map:
        self.update_known_addresses(sender_id, addrlist)
        yield env.timeout(random.randint(1, 2))
        # then choose 2 connected peers and forward the addresses,
        # unless the selected peers already know the address.
        if len(self.get_connected()) > 0:
            selected_peers = random.sample(self.get_connected(),min(2, len(self.get_connected())))
            logging.debug(f"Peer_{self.id} forwarding addr msg from {sender_id} to {selected_peers}")
            for peer_id in selected_peers:
                if peer_id not in self.addr_map:
                    self.addr_map[peer_id] = []
                if peer_id == sender_id:
                    continue  # do not forward to sending peers. They already have these nodes
                addrs2send = addrlist
                for addr in addrlist:
                    if addr in self.addr_map[peer_id]:
                        addrs2send.remove(addr)
                if len(addrs2send) > 0:
                    # update addr_map
                    self.update_addrmap(peer_id, addrlist)
                    # Send message to peer:
                    #peer = ALL_PEERS[peer_id]
                    #peer.receive_addr(self.id, addrs2send)
                    self.send_msg(peer_id, 'ADDR', addrs2send.copy())



    def receive_getaddr(self, sender_id):
        # the sending peer just joined the network
        # and asks for a list of ips to fill their addrman.
        # Reply with a random sample from known_addresses
        list2send = random.sample(self.known_peers, MAX_ADDR_SEND)
        peer = ALL_PEERS[sender_id]
        peer.receive_addr_list(self.id, list2send)

    def receive_addr_list(self, peer_id, addrlist):
        self.update_known_addresses(peer_id, addrlist)

    def departure(self):
        while True:
            # Wait for a departure event to occur
            yield env.timeout(random.expovariate(1.0 / self.departure_rate))

            if self.online == False:
                continue
            else:
                # Peer leaves the network
                self.online = False
                self.addr_map = {}
                logging.debug(f"{self.type} Peer_{self.id} left the network at time {env.now}")

                # Disconnect from all connected peers but in two steps: successors and predecessors in different steps
                # fisrt remove  and then
                ebunch = []
                copy_of_peers = list(G.successors(self.id)).copy()
                #for peer_id in G.successors(self.id): # outbound connection
                for peer_id in copy_of_peers:  # outbound connection
                    peer = ALL_PEERS[peer_id]
                    peer.disconnect_from_peer(self.id, outbound=True)
                    ebunch.append((self.id, peer_id))

                for peer_id in G.predecessors(self.id):
                    peer = ALL_PEERS[peer_id]
                    peer.disconnect_from_peer(self.id)
                    ebunch.append((peer_id, self.id))

                G.remove_edges_from(ebunch)
                G.remove_node(self.id)

                # Stop the peer's message sending process
                #self.periodic_addr_generation.interrupt()

                # Start the arrival process
                self.arrival_process = env.process(self.arrival())

    def disconnect_from_peer(self, peer_id, outbound=False):
        # Peer with id peer_id left the Network.
        # Disconnect from the specified peer
        if peer_id in self.addr_map:
            self.addr_map.pop(peer_id)

        if outbound:
            available_peers = list(set(self.known_peers.keys()) - set(self.get_connected()))
            needed_conns = self.num_peers - len(self.get_connected())
            if needed_conns > 0:
                selected_peers = random.sample(available_peers, min(needed_conns, len(available_peers)))
                for selected_id in selected_peers:
                    peer = ALL_PEERS[selected_id]
                    if peer.online:
                        G.add_edge(self.id, selected_id)
                        #logging.debug(f"Peer_{peer_id} disconnected from Peer {self.id}._______YXY_______ {self.id} created new connection to {selected_id} at time {env.now}")
                        #TODO: inform peer that we are now connected.

        #logging.debug(f"Peer {peer_id} disconnected from Peer {self.id} at time {env.now}")


    def connect_to_peer(self, peer_id):
        peer = ALL_PEERS[peer_id]


    def arrival(self):
        while self.arrival_rate>0:
            # Wait for an arrival event to occur
            yield env.timeout(random.expovariate(1.0 / self.arrival_rate))

            #assert self.online == False

            # Check if the peer is already online
            if not self.online:
                # Peer joins the network
                self.online = True
                self.net_connect_retries = 0
                logging.debug(f"Peer_{self.id} joined the network at time {env.now}")
                G.add_node(self.id)

                if len(self.known_peers) < 10:
                    logging.warning(f"Low number of KNOWN ADDRESSES")
                    self.seedGETADDR()

                self.connectToNetwork()

                # Start the peer's departure process
                if self.departure_rate > 0:
                    self.departure_process = env.process(self.departure())

                # Start the peer's message sending process
                # if self.message_rate > 0:
                #     logging.warning(f"self.periodic_addr_generation-->{self.periodic_addr_generation.ok}")
                #     self.periodic_addr_generation = env.process(self.addr_gen())
                #     logging.warning(f"self.periodic_addr_generation-->{self.periodic_addr_generation.is_alive}")
                #
                # # Stop the arrival process, already here
                # self.periodic_addr_generation.interrupt()

    def connectToNetwork(self):
        # logging.debug(f"Peer_{self.id}: TRYIN TO RECONNECT. current peers are {self.get_connected()}. NUM PEERS:{self.num_peers}")
        # # Connect to a random known peer
        # if self.net_connect_retries > 2:
        #     logging.error(f"Peer_{self.id} cannot connect to Network//Retried {self.net_connect_retries} times.")

        available_peers = list(set(self.known_peers.keys()) - set(self.get_connected()) - set([self.id]))
        if len(available_peers) < self.num_peers:
            #ask for more nodes:
            nodes_from_dns_seed = random.sample(list(G.nodes), int(G.number_of_nodes()/10))
            for node_id in nodes_from_dns_seed:
                if node_id == self.id:
                    continue
                self.known_peers[node_id] = env.now
                available_peers.append(node_id)

        random.shuffle(available_peers)
        needed_conns = self.num_peers - self.get_outboundN()
        established_conns = 0
        while len(available_peers) > 0:
            peer_id = available_peers.pop()
            peer = ALL_PEERS[peer_id]
            if peer.online:
                G.add_edge(self.id, peer_id)
                established_conns += 1
            if established_conns == needed_conns:
                break
            # TODO: inform peer that we are now connected.
            # TODO: when connecting send and addr message with our address.


        logging.debug(f"Peer_{self.id} CONNECTED TO {self.get_connected()}")


class BadPeer(Peer):
    """
    This peer does not relay address messages.
    They can receive addr and getaddr messages but do not reply
    In a more hostile setting instead of relayin addr messages they may send fake addresses,
    or  addresses controlled by an attacker.
    They may relay blocks and transactions.
    """
    type = 'BAD'

deg_seq = getDegreeDistribution('ba-model', NETWORK_SIZE)
ALL_PEERS = []

# Define the simulation environment
env = simpy.Environment()
comm_channel = BroadcastPipe(env)

# create peers:
for i in range(0, NETWORK_SIZE):
    num_neighbors = deg_seq.pop()
    #new_peer = GoodPeer(id=i, env=env, arrival_rate=2*ONE_HOUR, departure_rate=6*ONE_HOUR, message_rate=ONE_HOUR, num_peers = num_neighbors)
    new_peer = GoodPeer(id=i, env=env, arrival_rate=ONE_DAY, departure_rate=5*ONE_DAY, message_rate=ONE_DAY,
                        num_peers=num_neighbors, in_pipe=comm_channel.get_output_conn(), out_pipe=comm_channel)
    ALL_PEERS.append(new_peer)
    G.add_node(i)
    # TODO: use this randomness to create the percentage of bad peers.
    #  make sure the BAD peers play along correctly
    # _rand = random.random()
    # if _rand > 0.95:
    #     new_peer.departure_rate = ONE_DAY
    #     new_peer.arrival_rate = ONE_HOUR

for p in ALL_PEERS:
    num_neighbors = p.num_peers
    connected =  random.sample(ALL_PEERS, num_neighbors)
    for connected_peer in connected:
        G.add_edge(p.id, connected_peer.id)
        p.known_peers[connected_peer.id] = 0


def get_stats(env):
    logging.info(f"______________Hourly Stats at {env.now / ONE_HOUR} hours______________")
    logging.info(f"Graph Size: {nx.number_of_nodes(G)}")
    logging.info(f"Number of Edges: {G.number_of_edges()}")
    # logging.info(f"Degree Histogram: {nx.degree_histogram(G)}")
    logging.info(f"Graph density: {nx.density(G)}")
    # logging.info(f"Node Connectivity (approx.): {approx.node_connectivity(G)}")
    # logging.info(f"Avg Clustering (approx.): {approx.average_clustering(G, trials=1000, seed=10)}")
    # for n in ALL_PEERS:
    #     logging.info(f"{n}->{n.get_connected()}")
    logging.info(f"________________________________________________________")

def periodic_stat(env):
    while True:
        # Wait for a departure event to occur
        yield env.timeout(ONE_HOUR)
        get_stats(env)




# start nodes:
list(map(lambda node:node.startPeer(),ALL_PEERS))
env.process(periodic_stat(env))
env.run(until=2*ONE_DAY)

get_stats(env)