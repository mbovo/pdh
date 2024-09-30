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
import subprocess
from typing import Any, Dict, Iterator, List
from rich import print
from pdpyras import APISession, PDClientError
import json
from .config import Config


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

    def __init__(self, cfg: Config) -> None:
        super().__init__()

        self.cfg: Config = cfg
        self.session: APISession = APISession(cfg["apikey"], default_from=cfg["email"])
        self.session.max_network_attempts = 5
        self.users: list = list()
        self.incs: list = list()
        try:
            self.session.get("/users/me")
        except PDClientError as e:
            raise UnauthorizedException(str(e))


class Incidents(PD):
    def list(self, userid: list | None = None, statuses: list = DEFAULT_STATUSES, urgencies: list = DEFAULT_URGENCIES) -> List[Any]:
        """List all incidents"""
        params = {"statuses[]": statuses, "urgencies[]": urgencies}
        if userid:
            params["user_ids[]"] = userid
        return self.session.list_all("incidents", params=params)

    def mine(self, statuses: List = DEFAULT_STATUSES, urgencies: List = DEFAULT_URGENCIES) -> List:
        """List all incidents assigned to the configured UserID"""
        return self.list([self.cfg["uid"]], statuses, urgencies)

    def alerts(self, id: str) -> Dict | List:
        r = self.session.rget(f"/incidents/{id}/alerts")
        return r

    def get(self, id: str) -> Dict | List:
        """Retrieve a single incident by ID"""
        r = self.session.rget(f"/incidents/{id}")
        return r

    def ack(self, incs) -> None:
        self.change_status(incs, STATUS_ACK)

    def resolve(self, incs) -> None:
        self.change_status(incs, STATUS_RESOLVED)

    def change_status(self, incs, status: str = STATUS_ACK) -> None:
        for i in incs:
            if "status" in i:
                i["status"] = status

        self.bulk_update(incs)

    def snooze(self, incs, duration=14400) -> None:
        for i in incs:
            try:
                self.session.post(f"/incidents/{i['id']}/snooze", json={"duration": duration})
            except Exception as e:
                print(e)

    def bulk_update(self, incs):
        ret = None
        try:
            ret = self.session.rput("incidents", json=incs)
        except PDClientError as e:
            print(e)
        return ret

    def update(self, inc):
        ret = None
        try:
            ret = self.session.rput(f"/incidents/{inc['id']}", json=inc)
        except PDClientError as e:
            print(e)
        return ret

    def reassign(self, incs, uids: List[str]) -> None:
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

    def apply(self, incs, paths: List[str]) -> List:
        rets = []
        for script in paths:
            output = self.apply_single(incs, script)
            rets.append({"script": script} | output)
        return rets

    def apply_single(self, incs, script: str) -> Dict:
        process = subprocess.Popen(script, text=True, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = process.communicate(json.dumps(incs))
        process.wait()

        if process.returncode == 0:
            output = json.loads(stdout)
            if type(output) not in [dict, list, tuple]:
                output = {"output": str(output)}
            else:
                output = {"output": output}
        else:
            output = {"error": stderr}

        return output


class Users(PD):
    def list(self) -> List[Dict] | Iterator[Dict]:
        """List all users in PagerDuty account"""
        users = self.session.iter_all("users")

        return users

    def get(self, id: str) -> Dict | List:
        """Get a single user by ID"""
        return self.session.rget(f"/users/{id}")

    def search(self, query: str, key: str = "name") -> List[dict]:
        """Retrieve all users matching query on the attribute name"""

        def equiv(s) -> bool:
            return query.lower() in s[key].lower()

        users = [u for u in filter(equiv, self.session.iter_all("users"))]
        return users

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

class Services(PD):
    def list(self,params: dict | None = None) -> List[Dict] | Iterator[Dict]:
        """List all services in PagerDuty account"""
        if params:
            services = self.session.iter_all("services", params=params)
        else:
            services = self.session.iter_all("services")
        return services

    def get(self, id: str) -> Dict | List:
        """Get a single service by ID"""
        return self.session.rget(f"/services/{id}")

    def search(self, query: str, key: str = "name") -> List[dict]:
        """Retrieve all services matching query on the attribute name"""

        def equiv(s):
            return query.lower() in s[key].lower()

        services = [u for u in filter(equiv, self.session.iter_all("services"))]
        return services

    def serviceIDs(self, query: str, key: str = "name") -> List[str]:
        """Retrieve all serviceIDs matching query on the attribute name"""
        services = self.search(query, key)
        serviceIDs = [u["id"] for u in services]
        return serviceIDs
