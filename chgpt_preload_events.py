import simpy

def preload_events(env, events_dict):
    for node_id, timestamps in events_dict.items():
        for timestamp in timestamps:
            env.process(event_function(node_id, timestamp))

def event_function(node_id, timestamp):
    yield env.timeout(timestamp)
    print(f"Event occurred at node {node_id} at time {env.now}")

# Define the simulation environment
env = simpy.Environment()

# Define the dictionary of timestamps
events_dict = {
    1: [5, 10, 15],
    2: [3, 7, 12],
    3: [1, 6, 11],
}

# Pre-load the events
preload_events(env, events_dict)

# Start the simulation
env.run()


# 626590 is the first disconnection:
# so find all nodes that were online befor that
# and use those to form the initial network
