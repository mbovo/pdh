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
from typing import Any, Callable
from datetime import datetime, timezone
from rich.pretty import pretty_repr
from dikdik.dict import get_path


class Transformation(object):
    """
    Transformation is a collection of methods to transform dictionaries
    """
    @staticmethod
    def identity(field_name) -> Callable[..., Any]:
        def fun(i: dict) -> Any:
            return i[field_name]

        return fun

    @staticmethod
    def extract_date(item_name: str, format: str = "%Y-%m-%dT%H:%M:%SZ", tz: timezone | None = None) -> Callable[[dict], str]:
        def extract(i: dict) -> str:
            d = datetime.strptime(i[item_name], format)
            duration = datetime.now(tz) - d
            data = {}
            data["d"], remaining = divmod(duration.total_seconds(), 86_400)
            data["h"], remaining = divmod(remaining, 3_600)
            data["m"], _ = divmod(remaining, 60)

            time_parts = [f"{round(value)}{name}" for name, value in data.items() if value > 0]
            if time_parts:
                return " ".join(time_parts) + " ago"
            else:
                return "less than 1m ago"

        return extract

    @staticmethod
    def extract_field(field_name: str, color_map: dict | None = None, default_color: str | None  = None, change_map: dict | None = None, map_func: Callable[[str,dict],str] | None = None,) -> Callable[[dict],str]:
        """
        Returns an extracor function that must be used with Filter.do()
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
        def extract(i: dict) -> str:
            item = get_path(i, field_name)

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
                    ret = map_func(item,i)
                except Exception as e:
                    print(f"Error in map_func: {e}")

            if default_color:
                # if a default_color is defined, use it to color the output
                ret = f"[{default_color}]{ret}[/{default_color}]"

            return f"{ret}"

        return extract

    @staticmethod
    def extract_assignees(color: str = "magenta") -> Callable[[dict], str]:
        def extract(i: dict) -> str:
            return f'[{color}]{", ".join([a["assignee"]["summary"] for a in i["assignments"]])}[/{color}]'

        return extract

    @staticmethod
    def extract_alerts(field_name, alert_fields: list[str] = ["id", "summary", "created_at", "status"]):
        from jsonpath_ng import parse

        def extract(i: dict) -> str:
            alerts = i[field_name]
            ret = dict()
            for alert in alerts:
                alert_obj = dict()
                for field in alert_fields:
                    if field not in alert:
                        expression = parse(field)
                        alert_obj.update({field: match.value for match in expression.find(alert)})
                    else:
                        alert_obj[field] = alert[field]

                ret[alert["id"]] = alert_obj
            return pretty_repr(ret)

        return extract

    @staticmethod
    def extract_pending_actions():
        return lambda i: str([f"{a['type']} at {a['at']}" for a in i["pending_actions"]])

    @staticmethod
    def extract_users_teams():
        return lambda x: ",".join([t["summary"] for t in x["teams"]])

    @staticmethod
    def extract_path(path: str, errStr: str = 'unknown_field') -> Callable[[dict], str]:
        '''
            Extract the subfield the field dictionary

            field: the name of the field to extract
            subfield: the name of the subfield to extract

            given something like
            alert = {
                "field": {
                    "subfield": "value"
                }
            }
            extract_from_dict("alert.field.subfield") will produce "value"
        '''
        def extract(i: dict) -> str:
            try:
                return get_path(i, path)
            except KeyError:
                return errStr

        return extract
