ONE_SECOND = 1;
ONE_MINUTE = 60 * ONE_SECOND;
ONE_HOUR = 60 * ONE_MINUTE;
ONE_DAY = 24 * ONE_HOUR;

class Peer:
    def __init__(self, id, env):
        self.id = id
        self.online = False

    def __str__(self):
        return(f"Peer_{self.id}/{self.online}")


class GoodPeer(Peer):
    def __init__(self, id, env, arrival_rate, departure_rate, message_rate, num_peers):
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

        self.max_node_age = 6 * ONE_HOUR  # chosen arbitrarilly TODO: confirm from bitcoin core