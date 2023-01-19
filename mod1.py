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
                self.connect_to_peer(random.choice(self.known_peers))

                # Start the peer's departure process
                self.departure_process = env.process(self.departure())

                # Start the peer's message sending process
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
        while True:
            # Wait for a message event to occur
            yield env.timeout(random.expovariate(1.0 / self.message_rate))

            # Check if the peer is online
            if self.online:
                # Choose a random connected peer
                peer = random.choice(self.connected_peers)

                # Check if the chosen peer is online
                if peer.online:
                    # Peer sends a message to the chosen peer
                    print("Peer %d sent a message to Peer %d at time %d" % (self.id, peer.id, env.now))

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
