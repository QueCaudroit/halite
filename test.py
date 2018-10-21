import numpy as np

width = 7
height = 5
halite_array = np.random.randint(1000, size=(width, height))
n = 3

flat_array = halite_array.flatten()
flat_indices = flat_array.argsort()[len(flat_array) - n:]
best_pos = []
for i in flat_indices:
    best_pos.append((i // height, i % height))
print(best_pos)
print(halite_array)
