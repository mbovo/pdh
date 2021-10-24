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


class NPD(object):

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


class Incidents(NPD):
    def list(self, userid: list = None, statuses: list = DEFAULT_STATUSES, urgencies: list = DEFAULT_URGENCIES) -> List:
        """List all incidents"""
        params = {"statuses[]": statuses, "urgencies[]": urgencies}
        if userid:
            params["user_ids[]"] = userid
        self.incs = self.session.list_all("incidents", params=params)
        return self.incs

    def mine(self, statuses: list = DEFAULT_STATUSES, urgencies: list = DEFAULT_URGENCIES) -> List:
        """List all incidents assigned to the configured UserID"""
        return self.list([self.cfg["uid"]], statuses, urgencies)

    def get(self, id: str) -> dict:
        """Retrieve a single incident by ID"""
        r = self.session.rget(f"/incidents/{id}")
        return r

    def ack(self, ids: List):
        self.change_status(ids, STATUS_ACK)

    def resolve(self, ids: List):
        self.change_status(ids, STATUS_RESOLVED)

    def change_status(self, ids: List, status: str = STATUS_ACK):
        def f(s):
            return s["id"] in ids

        incs = [u for u in filter(f, self.incs)]

        for i in incs:
            i["status"] = status

        self.bulk_update(incs)

    def snooze(self, ids: List, duration=14400):
        def f(s):
            return s["id"] in ids

        incs = [u for u in filter(f, self.incs)]
        for i in incs:
            self.session.post(f"/incidents/{i['id']}/snooze", json={"duration": duration})

    def bulk_update(self, incs: List):
        return self.session.rput("incidents", json=incs)

    def update(self, inc):
        return self.session.rput(f"/incidents/{inc['id']}", json=inc)

    def reassign(self, ids: List[str], uids: List[str]):
        def f(s):
            return s["id"] in ids

        incs = [u for u in filter(f, self.incs)]

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


class Users(NPD):
    def list(self) -> list(dict()):
        """List all users in PagerDuty account"""
        users = self.session.iter_all("users")

        def teams_to_human(teams: dict):
            return ",".join([t["summary"] for t in teams])

        filtered = [
            {
                "id": u["id"],
                "name": u["name"],
                "email": u["email"],
                "time_zone": u["time_zone"],
                "role": u["role"],
                "job_title": u["job_title"],
                "teams": teams_to_human(u["teams"]),
            }
            for u in users
        ]
        return filtered

    def get(self, id: str) -> Dict:
        """Get a single user by ID"""
        return self.session.rget(f"/users/{id}")

    def search(self, query: str, key: str = "name") -> List[dict]:
        """Retrieve all users matching query on the attribute name"""

        def equiv(s):
            return query.lower() in s[key].lower()

        users = [u for u in filter(equiv, self.session.iter_all("users"))]
        return users

    def filter(
        self, query: str, key: str = "name", attributes: List[str] = ["id", "name", "email", "time_zone"]
    ) -> List[dict]:
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
