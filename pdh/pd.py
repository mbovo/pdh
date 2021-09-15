from typing import List
from pdpyras import APISession


class PD(object):

    session = None
    cfg = None

    def __init__(self, cfg: dict) -> None:
        super().__init__()
        if not self.session:
            self.cfg = cfg
            self.session = APISession(cfg["apikey"], default_from=cfg["email"])

    def list_incidents(self, userid: list = None, statuses: list = ["triggered", "acknowledged"]):
        params = {"statuses[]": statuses}
        if userid:
            params["user_ids[]"] = userid

        incs = self.session.list_all("incidents", params=params)

        return incs

    def list_my_incidents(self, statuses: list = ["triggered", "acknowledged"]):
        return self.list_incidents([self.cfg["uid"]], statuses)

    def get_user_names(self, incident: dict) -> List[str]:

        assignments = incident["assignments"]

        users = list()
        for a in assignments:
            users.append(a["assignee"]["summary"])

        return users
