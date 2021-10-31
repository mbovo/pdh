from typing import Dict, List
from pdpyras import APISession, PDClientError


class UnauthorizedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


URGENCY_HIGH = "high"
URGENCY_LOW = "low"
STATUS_TRIGGERED = "triggered"
STATUS_ACK = "acknowledged"
STATUS_RESOLVED = "resolved"

DEFAULT_STATUSES = [STATUS_TRIGGERED, STATUS_ACK]
DEFAULT_URGENCIES = [URGENCY_HIGH, URGENCY_LOW]


class PD(object):

    session = None
    cfg = None
    users = list()
    incs = list()

    def __init__(self, cfg: dict()) -> None:
        super().__init__()
        if not self.session:
            self.cfg = cfg
            self.session = APISession(cfg["apikey"], default_from=cfg["email"])
            try:
                self.session.get("/users/me")
            except PDClientError as e:
                raise UnauthorizedException(str(e))


class Incidents(PD):
    def list(self, userid: list = None, statuses: list = DEFAULT_STATUSES, urgencies: list = DEFAULT_URGENCIES) -> List:
        """List all incidents"""
        params = {"statuses[]": statuses, "urgencies[]": urgencies}
        if userid:
            params["user_ids[]"] = userid
        return self.session.list_all("incidents", params=params)

    def mine(self, statuses: list = DEFAULT_STATUSES, urgencies: list = DEFAULT_URGENCIES) -> List:
        """List all incidents assigned to the configured UserID"""
        return self.list([self.cfg["uid"]], statuses, urgencies)

    def get(self, id: str) -> dict:
        """Retrieve a single incident by ID"""
        r = self.session.rget(f"/incidents/{id}")
        return r

    def ack(self, incs: List):
        self.change_status(incs, STATUS_ACK)

    def resolve(self, incs: List):
        self.change_status(incs, STATUS_RESOLVED)

    def change_status(self, incs: List, status: str = STATUS_ACK):
        for i in incs:
            if "status" in i:
                i["status"] = status

        self.bulk_update(incs)

    def snooze(self, incs: List, duration=14400):
        for i in incs:
            self.session.post(f"/incidents/{i['id']}/snooze", json={"duration": duration})

    def bulk_update(self, incs: List):
        return self.session.rput("incidents", json=incs)

    def update(self, inc):
        return self.session.rput(f"/incidents/{inc['id']}", json=inc)

    def reassign(self, incs: List, uids: List[str]):
        for i in incs:
            assignments = [{"assignee": {"id": u, "type": "user_reference"}} for u in uids]
            new_inc = {
                "id": i["id"],
                "type": "incident_reference",
                "assignments": assignments,
            }
            try:
                self.session.rput(f"/incidents/{i['id']}", json=new_inc)
            except Exception as e:
                print(str(e))


class Users(PD):
    def list(self) -> list(dict()):
        """List all users in PagerDuty account"""
        users = self.session.iter_all("users")

        return users

    def get(self, id: str) -> Dict:
        """Get a single user by ID"""
        return self.session.rget(f"/users/{id}")

    def search(self, query: str, key: str = "name") -> List[dict]:
        """Retrieve all users matching query on the attribute name"""

        def equiv(s):
            return query.lower() in s[key].lower()

        users = [u for u in filter(equiv, self.session.iter_all("users"))]
        return users

    def filter(self, query: str, key: str = "name", attributes: List[str] = ["id", "name", "email", "time_zone"]) -> List[dict]:
        users = self.search(query, key)

        filtered = list()
        for u in users:
            f = dict()
            for attr in attributes:
                f[attr] = u[attr]
            filtered.append(f)

        return filtered

    def userIDs(self, query: str, key: str = "name") -> List[str]:
        """Retrieve all userIDs matching query on the attribute name"""
        users = self.search(query, key)
        userIDs = [u["id"] for u in users]
        return userIDs

    def userID_by_mail(self, query):
        """Retrieve all usersIDs matching the given (partial) email"""
        return self.userIDs(query, "email")

    def userID_by_name(self, query):
        """Retrieve all usersIDs matching the given (partial) name"""
        return self.userIDs(query, "name")


class Filter(object):
    def le(field: str, value: int):
        def f(item: dict) -> bool:
            if item[field] <= value:
                return True
            return False

        return f

    def ge(field: str, value: int):
        def f(item: dict) -> bool:
            if item[field] >= value:
                return True
            return False

        return f

    def lt(field: str, value: int):
        def f(item: dict) -> bool:
            if item[field] < value:
                return True
            return False

        return f

    def gt(field: str, value: int):
        def f(item: dict) -> bool:
            if item[field] > value:
                return True
            return False

        return f

    def inList(field: str, listOfValues: List[str]):
        def f(item: dict) -> bool:
            if item[field] in listOfValues:
                return True
            return False

        return f

    def inStr(field: str, value: str):
        def f(item: dict) -> bool:
            if value.lower() in item[field].lower():
                return True
            return False

        return f

    def ieq(field: str, value: str):
        def f(item: dict) -> bool:
            if item[field].lower() == value.lower():
                return True
            return False

        return f

    def eq(field: str, value: str):
        def f(item: dict) -> bool:
            if item[field] == value:
                return True
            return False

        return f

    def regexp(field: str, regexp):
        def f(item: dict) -> bool:
            if regexp.search(item[field]):
                return True
            return False

        return f

    def objects(objects: list, transformations: dict = {}, filters: list = []) -> list:
        """Give a list of objects, apply every transformations and filters on it, return the new filtered list
        Transformations is a dict of "key": func(item) where key is the destination key and func(item) the
                        function to used to extract values from the original list
        Filters is a list of functions in the form f(item:Any)->bool the item will be in the returned list
                        if the function returns True
        """
        ret = list()
        for obj in objects:
            item = {}
            for path, func in transformations.items():
                item[path] = func(obj)
            ret.append(item)
        for filter_func in filters:
            ret = [o for o in filter(filter_func, ret)]
        return ret


class Transformation(object):
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
