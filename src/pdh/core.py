from .transformations import Transformation
from .filters import Filter
from .pd import UnauthorizedException, Users, Incidents
from .config import Config
from .output import print, print_items


class PDH(object):
    def list_user(cfg: Config, output: str, fields: list = None) -> bool:
        try:
            if fields is None:
                fields = ["id", "name", "email", "time_zone", "role", "job_title", "teams"]

            if isinstance(fields, str):
                fields = fields.split(",")

            users = Users(cfg).list()

            if output == "raw":
                filtered = users
            else:
                t = {}
                for f in fields:
                    t[f] = Transformation.extract_field(f, check=False)
                if "teams" in fields:
                    t["teams"] = Transformation.extract_users_teams()
                filtered = Filter.do(users, t, [])

            print_items(filtered, output)
            return True
        except UnauthorizedException as e:
            print(f"[red]{e}[/red]")
            return False

    def get_user(cfg: Config, user: str, output: str, fields: list = None):
        try:
            u = Users(cfg)
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
                    transformations[t] = Transformation.extract_field(t, check=False)
                transformations["teams"] = Transformation.extract_users_teams()

                filtered = Filter.do(users, transformations, [])

            print_items(filtered, output)
            return True
        except UnauthorizedException as e:
            print(f"[red]{e}[/red]")
            return False

    def ack(cfg: Config, incIDs: list = []) -> None:
        pd = Incidents(cfg)
        incs = pd.list()
        incs = Filter.do(incs, filters=[Filter.inList("id", incIDs)])
        for i in incs:
            print(f"[yellow]✔[/yellow] {i['id']} [grey50]{i['title']}[/grey50]")
        pd.ack(incs)

    def resolve(cfg: Config, incIDs: list = []) -> None:
        pd = Incidents(cfg)
        incs = pd.list()
        incs = Filter.do(incs, filters=[Filter.inList("id", incIDs)])
        for i in incs:
            print(f"[green]✅[/green] {i['id']} [grey50]{i['title']}[/grey50]")
        pd.resolve(incs)

    def snooze(cfg: Config, incIDs: list = [], duration: int = 14400) -> None:
        pd = Incidents(cfg)
        import datetime

        incs = pd.list()
        incs = Filter.do(incs, filters=[Filter.inList("id", incIDs)])
        for id in incIDs:
            print(f"Snoozing incident {id} for { str(datetime.timedelta(seconds=duration))}")

        pd.snooze(incs, duration)

    def reassing(cfg: Config, incIDs: list = [], user: str = None):
        pd = Incidents(cfg)
        incs = pd.list()
        incs = Filter.do(incs, filters=[Filter.inList("id", incIDs)])

        users = Users(cfg).userID_by_name(user)
        if users is None or len(users) == 0:
            users = Users(cfg).userID_by_name(user)

        for id in incIDs:
            print(f"Reassign incident {id} to {users}")

        pd.reassign(incs, users)
