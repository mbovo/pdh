from typing import Any
from .pd import URGENCY_HIGH


class Transformation(object):
    """
    Transformation is a collection of methods to transform dictionaries
    """

    def identity(field_name):
        def fun(i: dict) -> Any:
            return i[field_name]

        return fun

    def extract_field(
        item_name: str,
        colors: list = ["red", "cyan"],
        check_field: str = "urgency",
        check_value: str = URGENCY_HIGH,
        check: bool = True,
    ):
        def extract(i: dict) -> str:
            if check:
                if i[check_field] == check_value:
                    return f"[{colors[0]}]{i[item_name]}[/{colors[0]}]"
                return f"[{colors[1]}]{i[item_name]}[/{colors[1]}]"
            else:
                return f"{i[item_name]}"

        return extract

    def extract_assignees(color: str = "magenta") -> str:
        def extract(i: dict) -> str:
            return f'[{color}]{", ".join([a["assignee"]["summary"] for a in i["assignments"]])}[/{color}]'

        return extract

    def extract_pending_actions():
        return lambda i: str([f"{a['type']} at {a['at']}" for a in i["pending_actions"]])

    def extract_users_teams():
        return lambda x: ",".join([t["summary"] for t in x["teams"]])
