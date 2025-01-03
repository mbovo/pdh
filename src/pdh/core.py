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
from .filters import Filter
from . import Transformations
from .pd import PagerDuty, UnauthorizedException
from .config import Config
from .output import print, print_items
from typing import List
from datetime import timezone

class PDH(object):

    @staticmethod
    def list_user(cfg: Config, output: str, fields: list | None = None) -> bool:
        try:
            if fields is None:
                fields = ["id", "name", "email", "time_zone", "role", "job_title", "teams"]

            if isinstance(fields, str):
                fields = fields.split(",")

            users = PagerDuty(cfg).users.list()

            if output == "raw":
                filtered = users
            else:
                t = {}
                for f in fields:
                    t[f] = Transformations.extract(f)
                if "teams" in fields:
                    t["teams"] = Transformations.extract_users_teams()
                filtered = Transformations.apply(users, t)

            print_items(filtered, output)
            return True
        except UnauthorizedException as e:
            print(f"[red]{e}[/red]")
            return False

    @staticmethod
    def get_user(cfg: Config, user: str, output: str, fields: list | None = None):
        try:
            u = PagerDuty(cfg).users
            users = u.search(user)
            if len(users) == 0:
                users = u.search(user, "id")

            if fields is None:
                fields = ["id", "name", "email", "time_zone", "role", "job_title"]

            if isinstance(fields, str):
                fields = fields.split(",")

            # Prepare to filter and transform
            if output == "raw":
                filtered = users
            else:
                transformations = {}
                for t in fields:
                    transformations[t] = Transformations.extract(t)
                transformations["teams"] = Transformations.extract_users_teams()

                filtered = Transformations.apply(users, transformations)

            print_items(filtered, output)
            return True
        except UnauthorizedException as e:
            print(f"[red]{e}[/red]")
            return False

    @staticmethod
    def list_teams(cfg: Config, mine: bool = True, output='table', fields=None) -> bool:
        try:
            pd = PagerDuty(cfg)
            if mine:
                teams = dict(pd.me)['teams'] if 'teams' in pd.me else []
            else:
                teams = pd.teams.list()

            # set fields that will be displayed
            if type(fields) is str:
                fields = fields.lower().strip().split(",")
            else:
                fields = ["id", "summary", "html_url"]

            def plain_print_f(i):
                s = ""
                for f in fields:
                    s += f"{i[f]}\t"
                print(s)

            if output != "raw":
                transformations = dict()

                for f in fields:
                    transformations[f] = Transformations.extract(f)

                filtered = Transformations.apply(teams, transformations)
            else:
                filtered = teams

            print_items(filtered, output, plain_print_f=plain_print_f)
            return True
        except UnauthorizedException as e:
            print(f"[red]{e}[/red]")
            return False

    @staticmethod
    def list_services(cfg: Config, output: str = 'table', fields: List | None = None, sort_by:  str| None = None, reverse_sort: bool = False, status: str = "active,warning,critical") -> bool:
        try:
            pd = PagerDuty(cfg)
            svcs = pd.services.list()

            svcs = Filter.apply(svcs, [Filter.inList("status", status.split(","))])

            # set fields that will be displayed
            if type(fields) is str:
                fields = fields.lower().strip().split(",")
            else:
                fields = ["id", "name", "description", "status","created_at", "updated_at", "html_url"]

            if output != "raw":
                transformations = dict()

                for f in fields:
                    transformations[f] = Transformations.extract(f)
                    # special cases
                    if f == "status":
                        transformations[f] = Transformations.extract_decorate("status", color_map={"active": "green", "warning": "yellow", "critical": "red", "unknown": "gray", "disabled": "gray"}, change_map={
                                                                            "active": "OK", "warning": "WARN", "critical": "CRIT", "unknown": "❔", "disabled": "off"})
                    if f == "url":
                        transformations[f] = Transformations.extract("html_url")
                    if f in ["created_at", "updated_at"]:
                        transformations[f] = Transformations.extract_date(
                            f, "%Y-%m-%dT%H:%M:%S%z", timezone.utc)

                filtered = Transformations.apply(svcs, transformations)
            else:
                # raw output, using json format
                filtered = svcs

            # define here how print in "plain" way (ie if output=plain)
            def plain_print_f(i):
                s = ""
                for f in fields:
                    s += f"{i[f]}\t"
                print(s)

            if sort_by:
                sort_fields: str | list[str] = sort_by.split(",") if ',' in sort_by else sort_by

                if isinstance(sort_fields, list) and len(sort_fields) > 1:
                    filtered = sorted(filtered, key=lambda x: [
                                    x[k] for k in sort_fields], reverse=reverse_sort)
                else:
                    filtered = sorted(
                        filtered, key=lambda x: x[sort_fields], reverse=reverse_sort)

            print_items(filtered, output, plain_print_f=plain_print_f)
            return True

        except UnauthorizedException as e:
                print(f"[red]{e}[/red]")
                return False
        except KeyError:
                print(f"[red]Invalid sort field: {sort_by}[/red]")
                ff = ", ".join(fields) if fields else ""
                print(f"[yellow]Available fields: {ff}[/yellow]")
                return False

    @staticmethod
    def ack(cfg: Config, incIDs: list = []) -> None:
        pd = PagerDuty(cfg)
        incs = pd.incidents.list()
        incs = Filter.apply(incs, filters=[Filter.inList("id", incIDs)])
        for i in incs:
            print(f"[yellow]✔[/yellow] {i['id']} [grey50]{i['title']}[/grey50]")
        pd.incidents.ack(incs)

    @staticmethod
    def resolve(cfg: Config, incIDs: list = []) -> None:
        pd = PagerDuty(cfg)
        incs = pd.incidents.list()
        incs = Filter.apply(incs, filters=[Filter.inList("id", incIDs)])
        for i in incs:
            print(f"[green]✅[/green] {i['id']} [grey50]{i['title']}[/grey50]")
        pd.incidents.resolve(incs)

    @staticmethod
    def snooze(cfg: Config, incIDs: list = [], duration: int = 14400) -> None:
        pd = PagerDuty(cfg)
        import datetime

        incs = pd.incidents.list()
        incs = Filter.apply(incs, filters=[Filter.inList("id", incIDs)])
        for id in incIDs:
            print(f"Snoozing incident {id} for { str(datetime.timedelta(seconds=duration))}")

        pd.incidents.snooze(incs, duration)

    @staticmethod
    def reassign(cfg: Config, incIDs: list = [], user: str | None = None):
        pd = PagerDuty(cfg)
        incs = pd.incidents.list()
        incs = Filter.apply(incs, filters=[Filter.inList("id", incIDs)])

        users = pd.users.id(user)
        if users is None or len(users) == 0:
            users = pd.users.id(user)

        for id in incIDs:
            print(f"Reassign incident {id} to {users}")

        pd.incidents.reassign(incs, users)
