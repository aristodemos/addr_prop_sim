import simpy
import random

# Define the simulation environment
env = simpy.Environment()


# Define the peer class
class Peer(object):
    def __init__(self, env, arrival_rate, departure_rate, message_rate, known_peers):
        self.env = env
        self.arrival_rate = arrival_rate
        self.departure_rate = departure_rate
        self.message_rate = message_rate
        self.online = False
        self.known_peers = known_peers
        self.connected_peers = []

        # Start the peer's arrival process
        self.arrival_process = env.process(self.arrival())

    def arrival(self):
        while True:
            # Wait for an arrival event to occur
            yield env.timeout(random.expovariate(1.0 / self.arrival_rate))

            # Check if the peer is already online
            if not self.online:
                # Peer joins the network
                self.online = True
                print("Peer %d joined the network at time %d" % (self.id, env.now))

                # Connect to a random known peer
                if len(self.known_peers) > 0:
                    self.connect_to_peer(random.choice(self.known_peers))

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
            print("Peer %d left the network at time %d" % (self.id, env.now))

            # Disconnect from all connected peers
            for peer in self.connected_peers:
                self.disconnect_from_peer(peer)

            # Stop the peer's message sending process
            self.message_process.interrupt()

    def send_message(self):
        while self.message_rate > 0:
            # Wait for a message event to occur
            yield env.timeout(random.expovariate(1.0 / self.message_rate))

            # Check if the peer is online
            if self.online:
                # Choose a random connected peer
                peer = random.choice(self.connected_peers)

                # Check if the chosen peer is online
                if peer.online:
                    # Peer sends a message to the chosen peer
                    peer.receive_message(self.id)
                    print("Peer %d sent a message to Peer %d at time %d" % (self.id, peer.id, env.now))

    def receive_message(self, sender_id):
        # Peer receives a message from the chosen peer
        print("Peer %d received a message from Peer %d at time %d" % (self.id, sender_id, env.now))

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


# Define the bad peer class
class BadPeer(object):
    def __init__(self, env, known_peers, id):
        self.env = env
        self.online = True
        self.known_peers = known_peers
        self.connected_peers = []
        self.id = id

        # Connect to a random known peer
        self.connect_to_peer(random.choice(self.known_peers))

        # Start the peer's message receiving process
        #self.message_process = env.process(self.receive_message())

    def receive_message(self, sender_id):
        # Peer receives a message from the chosen peer
        print("Peer %d received a message from Peer %d at time %d" % (self.id, sender_id, env.now))

    def connect_to_peer(self, peer):
        # Connect to the specified peer
        self.connected_peers.append(peer)
        peer.connected_peers.append(self)
        print("BadPeer %d connected to Peer %d at time %d" % (self.id, peer.id, env.now))


# Create the peers
NUM_PEERS=100
NUM_NEIGHBORING_PEERS=10

# Create the BAD peers
NUM_BAD_PEERS=100
NUM_BAD_NEIGHBORING_PEERS=20

NUM_BOOTSTRAP_PEERS = 15

peers = []

# Bootstrap peers
for i in range(NUM_BOOTSTRAP_PEERS):
    neighboring_peers = []
    # Create the peer
    peer = Peer(env, arrival_rate=10, departure_rate=0, message_rate=0, known_peers=neighboring_peers)
    peer.id = i
    peers.append(peer)


for i in range(NUM_BOOTSTRAP_PEERS, NUM_BOOTSTRAP_PEERS+NUM_PEERS):
    # Choose a random subset of the peers to be the neighboring peers for each peer
    neighboring_peers = random.sample(peers, k=NUM_NEIGHBORING_PEERS)

    # Create the peer
    peer = Peer(env, arrival_rate=10, departure_rate=5, message_rate=2, known_peers=neighboring_peers)
    peer.id = i
    peers.append(peer)

for i in range(NUM_BOOTSTRAP_PEERS+NUM_PEERS, NUM_BOOTSTRAP_PEERS+NUM_PEERS+NUM_BAD_PEERS):
    # Choose a random subset of the peers to be the neighboring peers for each peer
    neighboring_peers = random.sample(peers, k=NUM_BAD_NEIGHBORING_PEERS)

    # Create the peer
    peer = BadPeer(env, known_peers=neighboring_peers, id=i)
    #peer.id = i
    peers.append(peer)

# Run the simulation
env.run(until=1500)
