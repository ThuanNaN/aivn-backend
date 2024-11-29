import os
import random
import time
from bson import ObjectId

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


def convert_objectid_to_str(data):
    if isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    else:
        return data
    

def convert_id_to_id(data):
    if isinstance(data, list):
        return [convert_id_to_id(item) for item in data]
    elif isinstance(data, dict):
        return {convert_id_to_id(key): convert_id_to_id(value) for key, value in data.items()}
    elif isinstance(data, str):
        if data == "_id":
            return "id"
        return data
    else:
        return data
    

def cohort_permission(user_cohort: int | None,
                      cohorts: list[int] | None,
                      limit: bool = False
                      ) -> bool:
    """
    Check if user is allowed to access the resource based on cohort permissions.

    Args:

    user_cohort (int): The cohort of the user.
    cohorts (list): List of cohorts that are allowed to access the resource.
    limit (bool): If True, only the the cohorts in the list are allowed to access the resource.

    Returns:

    bool: True if the user is allowed to access the resource, False otherwise.
    """
    if cohorts is None:
        return True
    
    if user_cohort is None:
        return False
    
    in_cohorts = user_cohort in cohorts
    if limit:
        return in_cohorts
    
    if in_cohorts or user_cohort > max(cohorts):
        return True

    return False
