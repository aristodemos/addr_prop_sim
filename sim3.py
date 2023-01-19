import simpy
import random

# Define the simulation environment
env = simpy.Environment()

# Define the peer class
class Peer(object):
    def __init__(self, env, arrival_rate, departure_rate, message_rate, known_peers, peer_type):
        self.env = env
        self.arrival_rate = arrival_rate
        self.departure_rate = departure_rate
        self.message_rate = message_rate
        self.online = False
        self.known_peers = known_peers
        self.connected_peers = []
        self.peer_type = peer_type
        if self.peer_type == 'BAD':
            self.online = True

        # Start the connection process
        #self.maintain_connection_process = env.process(self.maintain_connection_process())
        # Start the peer's arrival process
        self.arrival_process = env.process(self.arrival())

        # Start the peer's message process
        self.message_process = env.process(self.send_message())

    # def maintain_connection_process(self):
    #     if self.id < 9:
    #         yield self.env.timeout(3)
    #     # tries to maintain at least 8 outbound connections
    #     while len(self.connected_peers) < 8 and len(self.known_peers)>8:
    #         self.connect_to_peer(random.choice(self.known_peers))

    # TODO: expire old disconnected peers.
    # TODO: message includes AddressList
    # TODO: on reception of AddressList send to 2 random nodes
    # TODO: on initial connection up to 1000 addresses in addrman

    def arrival(self):
        while self.arrival_rate>0:
            # Wait for an arrival event to occur
            yield env.timeout(random.expovariate(1.0 / self.arrival_rate))

            # Check if the peer is already online
            if not self.online:
                # Peer joins the network
                self.online = True
                print("Peer %d joined the network at time %d" % (self.id, env.now))

                # Connect to a random known peer
                if len(self.known_peers) > 0:
                    for i in range(8):
                        self.connect_to_peer(random.choice(self.known_peers))
                else:
                    print(f"POOR {self.peer_type} peer {self.id} doesn't know anyone...")

                # Start the peer's departure process
                if self.departure_rate > 0:
                    self.departure_process = env.process(self.departure())

                # Start the peer's message sending process
                if self.message_rate > 0:
                    self.message_process = env.process(self.send_message())

    def departure(self):
        while True:
            # Wait for a departure event to occur
            yield env.timeout(random.expovariate(1.0 / self.departure_rate))

            # Peer leaves the network
            self.online = False
            print(f"{self.peer_type} Peer {self.id} left the network at time {env.now}")

            # Disconnect from all connected peers
            for peer in self.connected_peers:
                self.disconnect_from_peer(peer)

            # Stop the peer's message sending process
            # try:
            #     self.message_process.interrupt()
            # except Exception as e:
            #     print(f"{e} || {self.peer_type}Peer {self.id}|{self.online}")
            #self.maintain_connection_process.interrupt()


    def send_message(self):
        while self.message_rate > 0 and len(self.connected_peers) > 0 and self.online:
            # Wait for a message event to occur
            try:
                yield env.timeout(random.expovariate(1.0 / self.message_rate))
            except simpy.Interrupt:
                # When we received an interrupt, we stop charging and
                # switch to the "driving" state
                print(f'{self.peer_type} Peer {self.id} Was interrupted.')

            # Check if the peer is online
            if self.online:
                if len(self.connected_peers) > 0:
                    # Choose a random connected peer
                    peer = random.choice(self.connected_peers)
                    # Check if the chosen peer is online
                    if peer.online:
                        # Peer sends a message to the chosen peer
                        peer.receive_message(self.id)
                        print(f"{self.peer_type} Peer {self.id} sent a message to Peer {peer.id} at time {env.now}")

    def receive_message(self, sender_id):
        # Peer receives a message from the chosen peer
        print(f"{self.peer_type} Peer {self.id} received a message from Peer {sender_id} at time {env.now}")

    def connect_to_peer(self, peer):
        # Connect to the specified peer
        self.connected_peers.append(peer)
        peer.connected_peers.append(self)
        print(f"Peer {self.id} connected to Peer {peer.id} at time {env.now}")

    def disconnect_from_peer(self, peer):
        # Disconnect from the specified peer
        self.connected_peers.remove(peer)
        peer.connected_peers.remove(self)
        print(f"Peer {self.id} disconnected from Peer {peer.id} at time {env.now}")


# Create the peers
NUM_PEERS=100
MAX_ADDR_LIST=500
DEFAULT_OUTBOUND = 8
# Create the BAD peers
NUM_BAD_PEERS=10
MAX_BAD_PEERS=20

peers = []
peer_no_neighbors = []
for i in range(NUM_PEERS):
    # Choose a random subset of the peers to be the neighboring peers for each peer
    if len(peers)>DEFAULT_OUTBOUND:
        neighboring_peers = random.sample(peers, k=DEFAULT_OUTBOUND)
        # Create the peer
        peer = Peer(env, arrival_rate=10, departure_rate=50, message_rate=5, known_peers=neighboring_peers,
                    peer_type='GOOD')
        peer.id = i
        peers.append(peer)
    else:
        peer = Peer(env, arrival_rate=10, departure_rate=50, message_rate=5, known_peers=[],
                    peer_type='GOOD')
        peer.id = i
        peers.append(peer)
        peer_no_neighbors.append(peer)

for peer in peer_no_neighbors:
    neighboring_peers = random.sample(peers, k=DEFAULT_OUTBOUND)
    peer.known_peers = neighboring_peers


for i in range(NUM_PEERS, NUM_PEERS+NUM_BAD_PEERS):
    # Choose a random subset of the peers to be the neighboring peers for each peer
    neighboring_peers = random.sample(peers, k=MAX_BAD_PEERS)

    # Create the peer
    peer = Peer(env, arrival_rate=0, departure_rate=0, message_rate=0, known_peers=neighboring_peers, peer_type='BAD')
    peer.id = i
    peers.append(peer)

# Run the simulation
env.run(until=60)