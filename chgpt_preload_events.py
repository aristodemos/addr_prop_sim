import simpy


def event_1_function():
    yield env.timeout(10)
    # Event logic
    print(f"event_1_function()@{env.now}")

def event_2_function():
    yield env.timeout(15)
    # Event logic
    print(f"event_2_function()@{env.now}")

def event_3_function():
    yield env.timeout(1)
    # Event logic
    print(f"event_3_function()@{env.now}")


# Define the simulation environment
env = simpy.Environment()

# Schedule an event to occur at time 10
event_1 = env.process(event_1_function())
#env.run(until=10)

# Schedule an event to occur at time 20
event_2 = env.process(event_2_function())
#env.run(until=20)

# Schedule an event to occur at time 30
event_3 = env.process(event_3_function())
#env.run(until=30)
event_1 = env.process(event_1_function())
# Start the simulation
env.run()


