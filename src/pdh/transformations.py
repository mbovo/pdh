from typing import Any
from .pd import URGENCY_HIGH
from datetime import datetime
import humanize
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
            return humanize.naturaltime(datetime.now() - d)

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
