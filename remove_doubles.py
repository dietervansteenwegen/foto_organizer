import os

with open('doubles.list') as f:
    for line in f:
        try:
            os.remove(line.strip())
        except FileNotFoundError:
            pass