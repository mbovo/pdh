#
# This file is part of the pdh (https://github.com/mbovo/pdh).
# Copyright (c) 2020-2023 Manuel Bovo.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import json
import sys
import functools
import subprocess
from typing import Union

from collections import namedtuple
from pdh import config, Incidents

ShellResponse = namedtuple("ShellResponse", "stdout stderr rc")


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


def exec(cmd: Union[str, list]) -> ShellResponse:
    """
    Runs any executable in a shell reeturning a ShellResponse(stdout,stderr,rc)
      Parameters:
        cmd (Union[str,list(str)]): Either a string or a list of strings with the command to run and its arguments
      Returns:
        ShellResponse: a namedtuple with three fields: stdout,stderr,rc with the relevant informations
    """
    p = subprocess.Popen(cmd, text=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    rc = p.returncode
    return ShellResponse(out, err, rc)


def chain(incs: list, path: str, pd: Incidents = None):
    """
    Chain loading another rule with the given list of incidents
      Parameters:
        incs (list): the list of incidents to pass through
        path (str): the path of the binary to call
        pd (Incidents): optional api instance, will be inistantiaed a brend new from default if not given
      Returns:
        A list of outputs
    """

    if pd is None:
        pd = api()

    ret = pd.apply_single(incs, path)
    if "output" in ret:
        return ret["output"]
    if "stderr" in ret:
        return ret["stderr"]
    return None


def api(config_file: str = "~/.config/pdh.yaml"):

    """
    Initializate the Pagerduty APIs in a more easy way
      Parameters:
        config_file (str): the file path with pdh configuration (defualt: ~/.config/pdh.yaml)
      Returns:
        Incidents (object): the api object capable of doing things
    """
    return Incidents(config.load_and_validate(config_file))
