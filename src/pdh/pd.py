#
# This file is part of the pdh (https://github.com/mbovo/pdh).
# Copyright (c) 2020-2025 Manuel Bovo.
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
from typing import Any, Dict, Iterator, List, Callable
from rich import print
from pagerduty import RestApiV2Client, Error
import json
from .config import Config
from functools import lru_cache
import time


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


def ttl_hash(seconds=30):
    return round(time.time() / seconds)


class RuleExecutionError(Exception):
    pass


class RuleInvalidOutput(TypeError):
    pass


class PagerDuty(object):

    # Expose the constants to the outside (rules)

    INCIDENT_STATUS_TRIGGERED = STATUS_TRIGGERED
    INCIDENT_STATUS_ACK = STATUS_ACK
    INCIDENT_STATUS_RESOLVED = STATUS_RESOLVED

    INCIDENT_URGENCY_HIGH = URGENCY_HIGH
    INCIDENT_URGENCY_LOW = URGENCY_LOW

    DEFAULT_STATUSES = DEFAULT_STATUSES
    DEFAULT_URGENCIES = DEFAULT_URGENCIES

    def __init__(self, cfg: Config) -> None:
        super().__init__()

        self.cfg: Config = cfg
        self.session: RestApiV2Client = RestApiV2Client(
            cfg["apikey"], default_from=cfg["email"])
        self.session.max_network_attempts = 5
        self.users = Users(self.cfg, self.session)
        self.services = Services(self.cfg, self.session)
        self.incidents = Incidents(self.cfg, self.session)
        self.teams = Teams(self.cfg, self.session)
        try:
            self.abilities: List | Dict = self.session.rget("/abilities")
        except Error as e:
            raise UnauthorizedException(str(e))
        try:
            self.me: List[Any] | Dict[Any,
                                      Any] = self.session.rget("/users/me")
        except Error:
            self.me = {}


class Incidents(object):

    def __init__(self, cfg: Config, session: RestApiV2Client) -> None:
        self.cfg = cfg
        self.session = session

    def list(self, userid: list | None = None, statuses: list = DEFAULT_STATUSES, urgencies: list = DEFAULT_URGENCIES, teams=None) -> List[Any]:
        """List all incidents"""
        params = {"statuses[]": statuses, "urgencies[]": urgencies}
        if userid:
            params["user_ids[]"] = userid
        if teams:
            params["team_ids[]"] = teams
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
                self.session.post(
                    f"/incidents/{i['id']}/snooze", json={"duration": duration})
            except Exception as e:
                print(e)

    def bulk_update(self, incs):
        ret = None
        try:
            ret = self.session.rput("incidents", json=incs)
        except Error as e:
            print(e)
        return ret

    def update(self, inc):
        ret = None
        try:
            ret = self.session.rput(f"/incidents/{inc['id']}", json=inc)
        except Error as e:
            print(e)
        return ret

    def reassign(self, incs, uids: List[str]) -> None:
        for i in incs:
            assignments = [
                {"assignee": {"id": u, "type": "user_reference"}} for u in uids]
            new_inc = {
                "id": i["id"],
                "type": "incident_reference",
                "assignments": assignments,
            }
            try:
                self.session.rput(f"/incidents/{i['id']}", json=new_inc)
            except Exception as e:
                print(str(e))

    def apply(self, incs: List[Any] | Dict[Any, Any] | Iterator[Any], paths: List[str], printFunc, errFunc: Callable) -> List[Any] | Dict[Any, Any] | Iterator[Any]:
        try:
            output = incs   # initial input
            for script in paths:
                # chain the output of the previous script to the input of the next
                output = self.apply_single(output, script)
                printFunc(script)
            return output
        except RuleExecutionError as e:
            errFunc(str(e))
        except RuleInvalidOutput as e:
            errFunc(str(e))
        return incs

    def apply_single(self, incs, script: str) -> Dict:
        process = subprocess.Popen(script, text=True, shell=True,
                                   stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = process.communicate(json.dumps(incs))
        process.wait()

        if process.returncode == 0:
            output = json.loads(stdout)
            if type(output) not in [dict, list, tuple]:
                raise RuleInvalidOutput(
                    f"invalid rule output it must be a json object, found: {type(output)}")
        else:
            raise RuleExecutionError(f"Error executing rule: {stderr}")

        return output


class Users(object):

    def __init__(self, cfg: Config, session: RestApiV2Client) -> None:
        self.cfg = cfg
        self.session = session

    @lru_cache()
    def list(self, ttl=ttl_hash()) -> List[Dict] | Iterator[Dict]:
        """List all users in PagerDuty account"""
        users = self.session.iter_all("users")

        return users

    @lru_cache()
    def get(self, id: str, ttl=ttl_hash()) -> Dict | List:
        """Get a single user by ID"""
        return self.session.rget(f"/users/{id}")

    @lru_cache()
    def search(self, query: str, key: str = "name", ttl=ttl_hash()) -> List[dict]:
        """Retrieve all users matching query on the attribute name"""

        def equiv(s) -> bool:
            return query.lower() in s[key].lower()

        users = [u for u in filter(equiv, self.session.iter_all("users"))]
        return users

    @lru_cache()
    def id(self, query: str, key: str = "name", ttl=ttl_hash()) -> List[str]:
        """Retrieve all userIDs matching query on the attribute name"""
        users = self.search(query, key)
        userIDs = [u["id"] for u in users]
        return userIDs

    @lru_cache()
    def id_by_email(self, query, ttl=ttl_hash()):
        """Retrieve all usersIDs matching the given (partial) email"""
        return self.id(query, "email")

    @lru_cache()
    def teams(self, name: str, ttl=ttl_hash()) -> List[Dict]:
        """Retrieve all teams for a given user"""
        users = self.search(query=name)
        teams = []
        for user in users:
            teams.append(user["teams"])
        return teams

    @lru_cache()
    def team_id(self, name: str, ttl=ttl_hash()) -> List[str]:
        """Retrieve all team IDs for a given user"""
        teams = self.teams(name)
        teamIDs = [team["id"] for team in teams]
        return teamIDs


class Services(object):

    def __init__(self, cfg: Config, session: RestApiV2Client) -> None:
        self.cfg = cfg
        self.session = session

    def list(self, params: dict | None = None) -> List[Dict] | Iterator[Dict]:
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

        services = [u for u in filter(
            equiv, self.session.iter_all("services"))]
        return services

    def id(self, query: str, key: str = "name") -> List[str]:
        """Retrieve all serviceIDs matching query on the attribute name"""
        services = self.search(query, key)
        serviceIDs = [u["id"] for u in services]
        return serviceIDs


class Teams(object):

    def __init__(self, cfg: Config, session: RestApiV2Client) -> None:
        self.cfg = cfg
        self.session = session

    @lru_cache()
    def list(self, ttl=ttl_hash()) -> List[Dict] | Iterator[Dict]:
        """List all teams in PagerDuty account"""
        users = self.session.iter_all("teams")

        return users

    @lru_cache()
    def get(self, id: str, ttl=ttl_hash()) -> Dict | List:
        """Get a single team by ID"""
        return self.session.rget(f"/teams/{id}")

    @lru_cache()
    def search(self, query: str, key: str = "name", ttl=ttl_hash()) -> List[dict]:
        """Retrieve all teams matching query on the attribute name"""

        def equiv(s) -> bool:
            return query.lower() in s[key].lower()

        teams = [u for u in filter(equiv, self.session.iter_all("teams"))]
        return teams

    @lru_cache()
    def id(self, query: str, key: str = "name", ttl=ttl_hash()) -> List[str]:
        """Retrieve all teams id matching query on the attribute name"""
        teams = self.search(query, key)
        teamids = [u["id"] for u in teams]
        return teamids
