# Auto-generated improvement — Iteration 34
# Suggestion: 1.  Remove unnecessary type hints in function signatures.

import math

def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

class Location:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Agent:
    def move(self, direction_x, direction_y):
        pass

def process_location(location):
    distance = calculate_distance(location.x, location.y, 0, 0)
    return f"distance: {distance}"

agent = Agent()
print(process_location(agent.Location(1, 2)))
