import os
import random
import time

def generate_id(length=8):
    """Generates a unique ID string using integers only.

    Args:
        length (int, optional): The desired length of the ID string. Defaults to 10.

    Returns:
        str: The generated ID string.
    """

    # Generate a random integer seed based on current time and process ID
    seed = int(time.time() * 1000) + os.getpid()
    random.seed(seed)

    # Generate a random integer within the desired range
    id_int = random.randint(10 ** (length - 1), 10 ** length - 1)

    # Convert the integer to a string and return it
    return str(id_int)