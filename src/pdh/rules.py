import json
import sys
import functools


def __load_data_from_stdin():
    return json.load(sys.stdin)


def rule(func):
    """
    Decorate a function transforming it into a Rule.

    The decorated function must have at least one parameters: `input` in which all the
    input data will be placed as dictionary. This will be the raw input data directly from PagerDuty APIs ready to use

    Each value returned by the decorated function will be used as output.
    If the returned object is a dict() the output will be passed as-is.
    Otherwise will be converted to string.

    """

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


def api(config_file: str = "~/.config/pdh.yaml"):

    """
    Initializate the Pagerduty APIs in a more easy way
      Parameters:
        config_file (str): the file path with pdh configuration (defualt: ~/.config/pdh.yaml)
      Returns:
        Incidents (object): the api object capable of doing things
    """

    from pdh import config, Incidents

    return Incidents(config.load_and_validate(config_file))
