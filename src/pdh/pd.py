from typing import List
from pdpyras import APISession, PDClientError


class UnauthorizedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class PD(object):

    session = None
    cfg = None

    def __init__(self, cfg: dict) -> None:
        super().__init__()
        if not self.session:
            self.cfg = cfg
            self.session = APISession(cfg["apikey"], default_from=cfg["email"])
            try:
                self.session.get("/users/me")
            except PDClientError as e:
                raise UnauthorizedException(str(e))

    def list_incidents(
        self, userid: list = None, statuses: list = ["triggered", "acknowledged"], urgencies: list = ["high", "low"]
    ):
        params = {"statuses[]": statuses, "urgencies[]": urgencies}
        if userid:
            params["user_ids[]"] = userid

        incs = self.session.list_all("incidents", params=params)

        return incs

    def list_my_incidents(self, statuses: list = ["triggered", "acknowledged"], urgencies: list = ["high", "low"]):
        return self.list_incidents([self.cfg["uid"]], statuses, urgencies)

    def get_incident(self, id: str) -> dict:
        r = self.session.rget(f"/incidents/{id}")
        return r

    def ack(self, inc):
        if inc["status"] != "acknowledged":
            inc["status"] = "acknowledged"
        return inc

    def resolve(self, i):
        if i["status"] == "acknowledged":
            i["status"] = "resolved"
        return i

    def snooze(self, i, duration=14400):
        if i["status"] == "acknowledged":
            self.session.post(f"/incidents/{i['id']}/snooze", json={"duration": duration})
        return i

    def update_incident(self, inc):
        return self.session.rput(f"/incidents/{inc['id']}", json=inc)

    def bulk_update_incident(self, incs):
        return self.session.rput("incidents", json=incs)

    def get_user_by(self, query: str, attribute: str = "name") -> List:
        equiv = lambda s: query.lower() in s[attribute].lower()
        users = [u for u in filter(equiv, self.session.iter_all("users"))]
        return users

    def get_userID_by(self, query: str, attribute: str = "name") -> List[str]:
        equiv = lambda s: query.lower() in s[attribute].lower()
        user = [u["id"] for u in filter(equiv, self.session.iter_all("users"))]
        return user

    def get_userID_by_email(self, query):
        return self.get_userID_by(query, "email")

    def get_userID_by_name(self, query):
        return self.get_userID_by(query, "name")

    def reassign(self, inc, users: List[str]):
        assignments = []
        for user in users:
            assignments.append({"assignee": {"id": user, "type": "user_reference"}})

        new_inc = {
            "id": inc["id"],
            "type": "incident_reference",
            "assignments": assignments,
        }
        return self.session.rput(f"/incidents/{inc['id']}", json=new_inc)


class User(object):
    def __init__(self, pd: PD = None, config: dict() = None) -> None:
        super().__init__()
        if config is not None:
            self.pd = PD(config)
            return
        if pd is not None:
            self.pd = pd
            return
        raise RuntimeError("You must initialize User class with a config or a PD object")

    def list(self) -> list(dict()):
        """List all users in PagerDuty account"""
        users = self.pd.session.iter_all("users")

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
