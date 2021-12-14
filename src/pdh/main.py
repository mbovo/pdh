import click
import pkg_resources
import yaml
import json
import sys
import re
from rich import print
from rich.table import Table
from rich.console import Console

from .pd import Users, UnauthorizedException, Incidents
from .pd import (
    STATUS_TRIGGERED,
    STATUS_ACK,
    URGENCY_HIGH,
    URGENCY_LOW,
    DEFAULT_URGENCIES,
)
from .transformations import Transformation
from .filters import Filter

import time
from .config import load_and_validate, setup_config

VALID_OUTPUTS = ["plain", "table", "json", "yaml", "raw"]


@click.group(help="PDH - PagerDuty for Humans")
def main():
    pass


@main.command(help="Create default configuration file")
@click.option(
    "-c",
    "--config",
    default="~/.config/pdh.yaml",
    help="Configuration file location (default: ~/.config/pdh.yaml)",
)
def config(config):
    setup_config(config)


@main.command(help="Print cloud tools version and exit")
def version():
    click.echo(f"v{pkg_resources.get_distribution('pdh').version}")


@main.group(help="Operater on Users")
@click.option(
    "-c",
    "--config",
    envvar="PDH_CONFIG",
    default="~/.config/pdh.yaml",
    help="Configuration file location (default: ~/.config/pdh.yaml)",
)
@click.pass_context
def user(ctx, config):
    cfg = load_and_validate(config)
    ctx.ensure_object(dict)
    ctx.obj = cfg


@user.command(help="List users", name="ls")
@click.pass_context
@click.option(
    "-o",
    "--output",
    "output",
    help="output format",
    required=False,
    type=click.Choice(VALID_OUTPUTS),
    default="table",
)
def user_list(ctx, output):
    try:
        u = Users(ctx.obj)
        users = u.list()

        transformations = {}
        for t in ["id", "name", "email", "time_zone", "role", "job_title"]:
            transformations[t] = Transformation.extract_field(t, check=False)
        transformations["teams"] = Transformation.extract_users_teams()
        filtered = Filter.objects(users, transformations, [])

        print_items(filtered, output)
    except UnauthorizedException as e:
        print(f"[red]{e}[/red]")
        sys.exit(1)


@user.command(help="Retrieve an user by name or ID", name="get")
@click.pass_context
@click.argument("user")
@click.option(
    "-o",
    "--output",
    "output",
    help="output format",
    required=False,
    type=click.Choice(VALID_OUTPUTS),
    default="table",
)
def user_get(ctx, user, output):
    try:
        u = Users(ctx.obj)
        # search by name
        users = u.search(user)
        if len(users) == 0:
            # if empty search by ID
            users = u.search(user, "id")

        # Prepare to filter and transform
        transformations = {}
        for t in ["id", "name", "email", "time_zone", "role", "job_title"]:
            # extract these fields from the original API response
            transformations[t] = Transformation.extract_field(t, check=False)
        transformations["teams"] = Transformation.extract_users_teams()

        filtered = Filter.objects(users, transformations, [])

        print_items(filtered, output)
    except UnauthorizedException as e:
        print(f"[red]{e}[/red]")
        sys.exit(1)


@main.group(help="Operater on Incidents")
@click.option(
    "-c",
    "--config",
    envvar="PDH_CONFIG",
    default="~/.config/pdh.yaml",
    help="Configuration file location (default: ~/.config/pdh.yaml)",
)
@click.pass_context
def inc(ctx, config):
    cfg = load_and_validate(config)
    ctx.ensure_object(dict)
    ctx.obj = cfg


@inc.command(help="Acknowledge specific incidents IDs")
@click.pass_context
@click.argument("incidentids", nargs=-1)
def ack(ctx, incidentids):
    pd = Incidents(ctx.obj)
    incs = pd.list()
    incs = Filter.objects(incs, filters=[Filter.inList("id", incidentids)])
    for id in incidentids:
        print(f"Mark {id} as [yellow]ACK[/yellow]")
    pd.ack(incs)


@inc.command(help="Resolve specific incidents IDs")
@click.pass_context
@click.argument("incidentids", nargs=-1)
def resolve(ctx, incidentids):
    pd = Incidents(ctx.obj)
    incs = pd.list()
    incs = Filter.objects(incs, filters=[Filter.inList("id", incidentids)])
    for id in incidentids:
        print(f"Mark {id} as [green]RESOLVED[/green]")
    pd.resolve(incs)


@inc.command(help="Snooze the incident(s) for the specified duration in seconds")
@click.pass_context
@click.option("-d", "--duration", required=False, default=14400, help="Duration of snooze in seconds")
@click.argument("incidentIDs", nargs=-1)
def snooze(ctx, incidentIDs, duration):
    pd = Incidents(ctx.obj)
    import datetime

    incs = pd.list()
    incs = Filter.objects(incs, filters=Filter.inList("id", incidentIDs))
    for id in incidentIDs:
        print(f"Snoozing incident {id} for { str(datetime.timedelta(seconds=duration))}")

    pd.snooze(incs, duration)


@inc.command(help="Re-assign the incident(s) to the specified user")
@click.pass_context
@click.option("-u", "--user", required=True, help="User name or email to assign to (fuzzy find!)")
@click.argument("incident", nargs=-1)
def reassign(ctx, incident, user):
    pd = Incidents(ctx.obj)
    incs = pd.list()
    incs = Filter.objects(incs, filters=Filter.inList("id", incident))

    users = Users(ctx.obj).userID_by_name(user)
    if users is None or len(users) == 0:
        users = Users(ctx.obj).userID_by_name(user)

    for id in incident:
        print(f"Reassign incident {id} to {users}")

    pd.reassign(incs, users)


@inc.command(help="List incidents", name="ls")
@click.pass_context
@click.option("-e", "--everything", help="List all incidents not only assigned to me", is_flag=True, default=False)
@click.option("-u", "--user", default=None, help="Filter only incidents assigned to this user ID")
@click.option("-n", "--new", is_flag=True, default=False, help="Filter only newly triggered incident")
@click.option("-a", "--ack", is_flag=True, default=False, help="Acknowledge incident listed here")
@click.option("-s", "--snooze", is_flag=True, default=False, help="Snooze for 4 hours incident listed here")
@click.option("-r", "--resolve", is_flag=True, default=False, help="Resolve the incident listed here")
@click.option("-h", "--high", is_flag=True, default=False, help="List only HIGH priority incidents")
@click.option("-l", "--low", is_flag=True, default=False, help="List only LOW priority incidents")
@click.option("-w", "--watch", is_flag=True, default=False, help="Continuosly print the list")
@click.option("-t", "--timeout", default=5, help="Watch every x seconds (work only if -w is flagged)")
@click.option("--raw", is_flag=True, default=False, help="output raw data from Pagerduty APIs")
@click.option("-R", "--regexp", default="", help="regexp to filter incidents")
@click.option(
    "-o",
    "--output",
    "output",
    help="output format",
    required=False,
    type=click.Choice(VALID_OUTPUTS),
    default="table",
)
def inc_list(ctx, everything, user, new, ack, output, snooze, resolve, high, low, watch, timeout, raw, regexp):

    # Prepare defaults
    status = [STATUS_TRIGGERED]
    urgencies = DEFAULT_URGENCIES
    if high:
        urgencies = [URGENCY_HIGH]
    if low:
        urgencies = [URGENCY_LOW]
    if not new:
        status.append(STATUS_ACK)
    userid = None
    if user:
        userid = Users(ctx.obj).userID_by_name(user)

    filter_re = None
    try:
        filter_re = re.compile(regexp)
    except Exception as e:
        print(f"[red]Invalid regular expression: {str(e)}[/red]")
        sys.exit(-2)

    incs = []
    pd = Incidents(ctx.obj)
    console = Console()
    while True:
        if everything or userid:
            incs = pd.list(userid, statuses=status, urgencies=urgencies)
        else:
            incs = pd.mine(statuses=status, urgencies=urgencies)

        ids = [i["id"] for i in incs]
        if snooze:
            pd.snooze(incs)
            if output not in ["yaml", "json"]:
                for i in ids:
                    print(f"Snoozing incident {i} for 4h")
        if resolve:
            pd.resolve(incs)
            if output not in ["yaml", "json"]:
                for i in ids:
                    print(f"Mark {i} as [green]RESOLVED[/green]")
        if ack:
            pd.ack(incs)
            if output not in ["yaml", "json"]:
                for i in ids:
                    print(f"Marked {i} as [yellow]ACK[/yellow]")

        # Build filtered list for output
        if raw:
            filtered = incs
            # Switch to raw output if you choose table or plain
            if output in ["plain", "table"]:
                output = "raw"
        else:
            transformations = {
                "id": Transformation.extract_field("id", check=False),
                "assignee": Transformation.extract_assignees(),
                "urgency": Transformation.extract_field("urgency"),
                "title": Transformation.extract_field("title"),
                "status": Transformation.extract_field("status", ["red", "yellow"], "status", STATUS_TRIGGERED, True),
                "url": Transformation.extract_field("html_url", check=False),
                # TODO: compose this dict dynamically with interesting Transformations instead of filtering out the output
                # 'pending_actions': Transformation.extract_pending_actions(),
                # 'created_at': Transformation.extract_field('created_at', check=False)
            }
            filtered = Filter.objects(incs, transformations, filters=[Filter.regexp("title", filter_re)])

        def plain_print(i):
            print(f"{i['assignee']}\t{i['status']}\t{i['title']}\t{i['url']}")

        print_items(filtered, output, plain_print_f=plain_print)
        if not watch:
            break
        time.sleep(timeout)
        console.clear()


def print_items(items, output, skip_columns: list = [], plain_print_f=None, console: Console = Console()) -> None:

    if output == "plain":
        for i in items:
            if plain_print_f:
                plain_print_f(i)
            else:
                console.print(i)
    elif output == "raw":
        console.print(items)
    elif output == "yaml":
        console.print(yaml.safe_dump(items))
    elif output == "json":
        console.print(json.dumps(items))
    elif output == "table" and len(items) > 0:
        table = Table(show_header=True, header_style="bold magenta")
        for k, _ in items[0].items():
            if k not in skip_columns:
                table.add_column(k)
        i = 0
        for u in items:
            args = [v for k, v in u.items() if k not in skip_columns]
            if i % 2:
                table.add_row(*args, style="grey93 on black")
            else:
                table.add_row(*args, style="grey50 on black")
            i += 1

        console.print(table)
