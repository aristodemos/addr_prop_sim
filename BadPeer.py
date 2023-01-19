import simpy
import random

# Define the simulation environment
env = simpy.Environment()


# Define the bad peer class
class BadPeer(object):
    def __init__(self, env, known_peers):
        self.env = env
        self.online = True
        self.known_peers = known_peers
        self.connected_peers = []

        # Connect to a random known peer
        self.connect_to_peer(random.choice(self.known_peers))

        # Start the peer's message receiving process
        self.message_process = env.process(self.receive_message())

    def receive_message(self):
        while True:
            # Wait for a message event to occur
            yield env.timeout(random.expovariate(1.0 / self.message_rate))

            # Check if the peer is online
            if self.online:
                # Choose a random connected peer
                peer = random.choice(self.connected_peers)

                # Check if the chosen peer is online
                if peer.online:
                    # Peer receives a message from the chosen peer
                    print("Peer %d received a message from Peer %d at time %d" % (self.id, peer.id, env.now))

    def connect_to_peer(self, peer):
        # Connect to the specified peer
        self.connected_peers.append(peer)
        peer.connected_peers.append(self)
        print("Peer %d connected to Peer %d at time %d" % (self.id, peer.id, env.now))
