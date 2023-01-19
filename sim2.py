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

        # Start the peer's arrival process
        self.arrival_process = env.process(self.arrival())

        # Start the peer's message process
        self.message_process = env.process(self.send_message())

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
                    for i in range(NUM_NEIGHBORING_PEERS):
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
            try:
                self.message_process.interrupt()
            except Exception as e:
                print(f"{e} || {self.peer_type}Peer {self.id}|{self.online}")


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
        print("Peer %d connected to Peer %d at time %d" % (self.id, peer.id, env.now))

    def disconnect_from_peer(self, peer):
        # Disconnect from the specified peer
        self.connected_peers.remove(peer)
        peer.connected_peers.remove(self)
        print("Peer %d disconnected from Peer %d at time %d" % (self.id, peer.id, env.now))


# Create the peers
NUM_PEERS=100
NUM_NEIGHBORING_PEERS=5

# Create the BAD peers
NUM_BAD_PEERS=10
NUM_BAD_NEIGHBORING_PEERS=20

peers = []
for i in range(NUM_PEERS):
    # Choose a random subset of the peers to be the neighboring peers for each peer
    if len(peers)>NUM_NEIGHBORING_PEERS:
        neighboring_peers = random.sample(peers, k=NUM_NEIGHBORING_PEERS)
    else:
        neighboring_peers = []

    # Create the peer
    peer = Peer(env, arrival_rate=2, departure_rate=20, message_rate=2, known_peers=neighboring_peers, peer_type='GOOD')
    peer.id = i
    peers.append(peer)

for i in range(NUM_PEERS, NUM_PEERS+NUM_BAD_PEERS):
    # Choose a random subset of the peers to be the neighboring peers for each peer
    neighboring_peers = random.sample(peers, k=NUM_BAD_NEIGHBORING_PEERS)

    # Create the peer
    peer = Peer(env, arrival_rate=0, departure_rate=0, message_rate=0, known_peers=neighboring_peers, peer_type='BAD')
    peer.id = i
    peers.append(peer)

# Run the simulation
env.run(until=60)