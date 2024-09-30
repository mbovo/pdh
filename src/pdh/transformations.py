#
# This file is part of the pdh (https://github.com/mbovo/pdh).
# Copyright (c) 2020-2024 Manuel Bovo.
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
from typing import Any, Callable, Dict, Iterator, List
from datetime import datetime, timezone
from rich.pretty import pretty_repr
from dikdik import Dict as DikDik

"""
  Transformations module contains functions to extract and mutate dictionary fields.
  Almost all functions here are meant to be used with apply() function
"""


def apply(objects: List[Any] | List[Dict[Any, Any]] | Iterator[Any], transformers: Dict[str, Callable[[Dict], Any]] | None = None, preserve: bool = False) -> List[Any] | List[Dict[Any, Any]] | Iterator[Any]:
    """
    Apply a set of transformation functions to a list or iterator of objects.

    Args:
      objects (List[Any] | List[Dict[Any, Any]] | Iterator[Any]):
        A list or iterator of objects to be transformed.
      transformers (Dict[str, Callable[[Dict], Any]] | None, optional):
        A dictionary where keys are paths and values are functions to be applied to the objects.
        Defaults to None.
      copy (bool, optional):
        If True, preserve the original fields if not mutated by a transformations function.
        Defaults to False.

    Returns:
      List[Any] | List[Dict[Any, Any]] | Iterator[Any]:
        A list or iterator of transformed objects.
    """
    ret = list()

    for obj in objects:
        if transformers is not None:
            item = obj if preserve else {}
            for path, func in transformers.items():
                DikDik.set_path(item, path, func(obj))
            ret.append(item)
        else:
            ret.append(obj)

    return ret

def extract(path: str, default: str | None = None) -> Callable[[Dict,], Any]:
    """
    Extracts a value from a dictionary based on a specified field path dot separated.
    If default is not specified, it will raise a KeyError when the field is not found.
    Args:
      field_name (str): The name of the field to extract. Can be a nested field in the form of "field.subfield".
      default    (str): The default value to return if the field is not found. Defaults to None.
    Returns:
      Callable[..., Any]: A function that takes a dictionary and returns the value of the specified field.
    """
    return extract_change(path, default=default, change_map=None)


def extract_change(path: str, change_map: Dict[str, str] | None = None, default: str|None = None) -> Callable[[Dict,], Any]:
    """
    Extracts a value from a dictionary based on a specified path and optionally maps it to a new value.
    Args:
      path (str): The path to the desired value in the dictionary, using dot notation for nested fields.
      change_map (Dict[str, str], optional): A dictionary mapping original values to new values. Defaults to None.
      default (str, optional): A default value to return if the specified path does not exist in the dictionary. Defaults to None.
    Returns:
      Callable[[Dict], Any]: A function that takes a dictionary and returns the extracted (and possibly mapped) value.
    Raises:
      KeyError: If the specified path does not exist in the dictionary and no default value is provided.
    """
    def f(i: dict) -> Any:
        try:
            # recursively return inner fields if they exist in the form of "field.subfield"
            ret = DikDik.get_path(i, path)
            if change_map and ret in change_map.keys():
                return change_map[ret]
            return ret
        except KeyError as e:
            if default:
                return default
            raise e

    return f


def extract_date(field_name: str, format: str = "%Y-%m-%dT%H:%M:%SZ", tz: timezone | None = None) -> Callable[[Dict], str]:
    """
    Converts a date string from a dictionary into a human-readable relative time format.
      - item_name (str): The key in the dictionary containing the date string.
      - format (str, optional): The format of the date string. Defaults to "%Y-%m-%dT%H:%M:%SZ".
      - tz (timezone, optional): The timezone to use for the current time. Defaults to None.
      - Callable[[Dict], Any]: A function that takes a dictionary and returns a human-readable relative time string.
    """
    def f(i: dict) -> str:
      val = DikDik.get_path(i, field_name)
      duration = datetime.now(tz) - datetime.strptime(val, format)
      date = {}
      date["d"], remaining = divmod(duration.total_seconds(), 86_400)
      date["h"], remaining = divmod(remaining, 3_600)
      date["m"], date["s"] = divmod(remaining, 60)

      time_parts = [f"{round(value)}{name}" for name,
                    value in date.items() if value > 0]
      if time_parts:
          return " ".join(time_parts) + " ago"
      else:
          return f"{date['s']}s ago"
    return f


def extract_decorate(field_name: str, color_map: dict | None = None, default_color: str | None = None, change_map: dict | None = None, map_func: Callable[[str, dict], str] | None = None,) -> Callable[[dict], str]:
    """
    Retrieve a specific field by name and optionally apply color and formatting.
    Optionally accept a map_func function to change the field value with custom logic

    Parameters:
    - field_name (str): The name of the field to extract.
    - color_map (dict, optional): A dictionary mapping field values to color codes for formatting.
    - default_color (str, optional): A default color code to apply to the field value.
    - change_map (dict, optional): A dictionary mapping original field values to new values.
    - map_func (Callable, optional): A function to apply to the field value for further transformation. Function must be in the form of `func(item:str, d: dict) -> str`

    Returns:
    - Callable: A function that takes a dictionary and returns the transformed field value as a string.
    """
    def f(i: dict) -> str:
        item = DikDik.get_path(i, field_name)

        if not item:
            return ""
        # escape [ and ] to avoid rich formatting clashes
        if '[' in item or ']' in item:
            ret = f"{item}".replace("[", "\\[")
        else:
            ret = item

        if change_map:
            # swap the real value with the one in the change_map
            if item in change_map.keys():
                ret = change_map[item]

        if color_map and item in color_map.keys():
            ret = f"[{color_map[item]}]{ret}[/{color_map[item]}]"

        if map_func is not None:
            # if a map_func is defined, use it to transform the output
            try:
                ret = map_func(item, i)
            except Exception as e:
                print(f"Error in map_func: {e}")

        if default_color:
            # if a default_color is defined, use it to color the output
            ret = f"[{default_color}]{ret}[/{default_color}]"

        return f"{ret}"

    return f


def extract_assignees(color: str = "magenta") -> Callable[[dict], str]:
  def f(i: dict) -> str:
    return f'[{color}]{", ".join([a["assignee"]["summary"] for a in i["assignments"]])}[/{color}]'
  return f


def extract_alerts(field_name, alert_fields: list[str] = ["id", "summary", "created_at", "status"]):
    def f(i: dict) -> str:
        alerts = DikDik.get_path(i, field_name)
        ret = dict()
        for alert in alerts:
            alert_obj = dict()
            for field in alert_fields:
                DikDik.set_path(alert_obj, field, DikDik.get_path(alert, field))

            ret[alert["id"]] = alert_obj
        return pretty_repr(ret)

    return f

def extract_pending_actions() :
    return lambda i: str([f"{a['type']} at {a['at']}" for a in i["pending_actions"]])

def extract_users_teams():
    return lambda x: ",".join([t["summary"] for t in x["teams"]])
