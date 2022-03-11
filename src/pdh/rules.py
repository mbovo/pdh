import json
import sys
import functools


def __load_data_from_stdin():
    return json.load(sys.stdin)


def rule(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        input = __load_data_from_stdin()
        kwargs["input"] = input
        ret = func(*args, **kwargs)
        print(json.dumps(ret))
        return ret

    return wrapper


def output(*args):
    pass
