import simpy
import random

RANDOM_SEED = 42
SIM_TIME = 100

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


def message_generator(name, env, out_pipe):
    while True:
        yield env.timeout(random.randint(6, 10))

        if random.random() < 0.5:
            id = 0
        else:
            id = 1

        msg = (id,env.now, f"{name} says hello at {env.now}")
        out_pipe.put(msg)
        print("++++++++++++++++++++++++++++++++++++++++++++++")


def message_consumer(name, env, in_pipe, id):
    while True:
        #msg = yield in_pipe.get()
        msg = yield in_pipe.get(lambda msg_rxed:  msg_rxed[0]==id)

        if msg[1] < env.now:
            print(f"LATE Getting msg: at time {env.now} {name} received {msg[1]}")
        else:
            print(f"at time {env.now} {name} received {msg[1]}")

        yield env.timeout(random.randint(4, 8))

# Setup and start the simulation
print('Process communication')
random.seed(RANDOM_SEED)
# env = simpy.Environment()

# For one-to-one or many-to-one type pipes, use Store
# pipe = simpy.Store(env)
# env.process(message_generator('Generator A', env, pipe))
# env.process(message_consumer('Consumer A', env, pipe))
#
# print('\nOne-to-one pipe communication\n')
# env.run(until=SIM_TIME)

# For one-to many use BroadcastPipe
# (Note: could also be used for one-to-one,many-to-one or many-to-many)
env = simpy.Environment()
bc_pipe = BroadcastPipe(env)

env.process(message_generator('Generator A', env, bc_pipe))
for i in range(0, 100):
    env.process(message_consumer(f'Consumer-{i} ', env, bc_pipe.get_output_conn(), i % 2))


print('\nOne-to-many pipe communication\n')
env.run(until=SIM_TIME)