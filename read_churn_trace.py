import pickle

with open('churntrace.txt', 'r') as h:
    lines = h.readlines()

d = {}
min_time = 1495384334
for l in lines:
    ts, node_id, state = l.strip().split('\t')
    if node_id not in d:
        d[node_id] = []
    if len(d[node_id]) > 0:
        d[node_id].append(int(ts) - min_time)
    else:
        d[node_id].append(int(ts) - min_time)

print(f"{len(d)}")
"""
40 = [35, 1038780, 1038846, 1056938, 1056953, 1123931, 1123938, 1230017, 1230024]
"""

with open('churntrace.pickle', 'wb') as h:
    pickle.dump(d, h)

# d = {}
# min_time = 1495384334
# for l in lines:
#     ts, node_id, state = l.strip().split('\t')
#     if node_id not in d:
#         d[node_id] = []
#     if len(d[node_id]) > 0:
#         d[node_id].append(int(ts) - min_time - d[node_id][-1])
#     else:
#         d[node_id].append(int(ts) - min_time)
#
# print(f"{len(d)}")
# """
# 40 = [35, 1038780, 1038846, 1056938, 1056953, 1123931, 1123938, 1230017, 1230024]
# """
#
# with open('churntrace.pickle', 'wb') as h:
#     pickle.dump(d, h)
