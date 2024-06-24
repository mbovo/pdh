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
from typing import Any
from .pd import URGENCY_HIGH
from datetime import datetime
from rich.pretty import pretty_repr


class Transformation(object):
    """
    Transformation is a collection of methods to transform dictionaries
    """

    def identity(field_name):
        def fun(i: dict) -> Any:
            return i[field_name]

        return fun

    def extract_date(item_name: str, format: str = "%Y-%m-%dT%H:%M:%SZ"):
        def extract(i: dict) -> str:
            d = datetime.strptime(i[item_name], format)
            duration = datetime.utcnow() - d
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

    def extract_field(
        item_name: str,
        colors: list = ["red", "cyan"],
        check_field: str = "urgency",
        check_value: str = URGENCY_HIGH,
        check: bool = False,
        change_dict: dict = None,
    ):
        def extract(i: dict) -> str:
            item = i[item_name]
            if change_dict is not None:
                if i[item_name] in change_dict.keys():
                    item = change_dict[i[item_name]]
            if check:
                if i[check_field] == check_value:
                    if item[0] != "[":
                        item = f"{item}".replace("[", "\\[")  # escape [ and ] to avoid rich formatting
                    return f"[{colors[0]}]{item}[/{colors[0]}]"
                return f"[{colors[1]}]{item}[/{colors[1]}]"
            else:
                return f"{item}"

        return extract

    def extract_assignees(color: str = "magenta") -> str:
        def extract(i: dict) -> str:
            return f'[{color}]{", ".join([a["assignee"]["summary"] for a in i["assignments"]])}[/{color}]'

        return extract

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

    def extract_pending_actions():
        return lambda i: str([f"{a['type']} at {a['at']}" for a in i["pending_actions"]])

    def extract_users_teams():
        return lambda x: ",".join([t["summary"] for t in x["teams"]])

    def extract_from_dict(field:str, subfield:str , errStr:str = 'unknown_field') -> str:
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
            extract_from_dict("field", "subfield")(alert) -> "value"
        '''
        def extract(i: dict) -> str:
            if field not in i:
                return errStr
            if i[field] is not None and isinstance(i[field], dict):
                if i[field][subfield] is not None:
                    if isinstance(i[field][subfield], str):
                        return i[field][subfield]
                    else:
                        return str(i[field][subfield])
            return ""
        return extract
