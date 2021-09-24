import click
import pkg_resources
import yaml
import json
import sys
from rich import print
from rich.live import Live
from rich.table import Table
from rich.console import Console
from .pd import PD, UnauthorizedException
import time
from .config import load_and_validate, setup_config


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


@user.command(help="Operate on users", name="get")
@click.pass_context
@click.argument("user")
@click.option(
    "-o",
    "--output",
    "output",
    help="output format",
    required=False,
    type=click.Choice(["table", "yaml", "json", "plain"]),
    default="table",
)
def user_get(ctx, user, output):
    try:
        pd = PD(ctx.obj)
    except UnauthorizedException as e:
        print(f"[red]{e}[/red]")
        sys.exit(1)

    users = pd.get_user_by(user)
    filtered = [{"id": u["id"], "name": u["name"], "email": u["email"], "time_zone": u["time_zone"]} for u in users]

    if output == "plain":
        for i in filtered:
            urgency_c = "cyan"
            if i["urgency"] == "high":
                urgency_c = "red"
            status_c = "green"
            if i["status"] == "triggered":
                status_c = "red"
            print(
                f"[magenta]{i['assignee']}[/magenta] [{status_c}]{i['status']}[/{status_c}] [{urgency_c}]{i['title']}[/{urgency_c}]  {i['url']}"
            )
    elif output == "yaml":
        print(yaml.safe_dump(filtered))
    elif output == "json":
        print(json.dumps(filtered))
    elif output == "table" and len(filtered) > 0:
        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        for k, _ in filtered[0].items():
            table.add_column(k)
        for u in filtered:
            table.add_row(u["id"], u["name"], u["email"], u["time_zone"])
        console.print(table)


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
@click.argument("incident", nargs=-1)
def ack(ctx, incident):
    pd = PD(ctx.obj)
    for id in incident:
        i = pd.get_incident(id)
        pd.ack(i)
        print(f"Mark {i['id']} [cyan]{i['title']}[/cyan] as [yellow]ACK[/yellow]")
        pd.update_incident(i)


@inc.command(help="Resolve specific incidents IDs")
@click.pass_context
@click.argument("incident", nargs=-1)
def resolve(ctx, incident):
    pd = PD(ctx.obj)
    for id in incident:
        i = pd.get_incident(id)
        pd.resolve(i)
        print(f"Mark {i['id']} [cyan]{i['title']}[/cyan] as [green]RESOLVED[/green]")
        pd.update_incident(i)


@inc.command(help="Snooze the incident(s) for the specified duration in seconds")
@click.pass_context
@click.option("-d", "--duration", required=False, default=14400, help="Duration of snooze in seconds")
@click.argument("incident", nargs=-1)
def snooze(ctx, incident, duration):
    pd = PD(ctx.obj)
    import datetime

    for id in incident:
        i = pd.get_incident(id)
        print(f"Snoozing incident {i['id']} for { str(datetime.timedelta(seconds=duration))}")
        pd.snooze(i, duration)


@inc.command(help="Re-assign the incident(s) to the specified user")
@click.pass_context
@click.option("-u", "--user", required=True, help="User name or email to assign to (fuzzy find!)")
@click.argument("incident", nargs=-1)
def reassign(ctx, incident, user):
    pd = PD(ctx.obj)

    users = pd.get_userID_by_name(user)
    if users is None or len(users) == 0:
        users = pd.get_userID_by_email(user)

    for id in incident:
        i = pd.get_incident(id)
        print(f"Reassign incident {i['id']} to {users}")
        print(pd.reassign(i, users))


@inc.command(help="List incidents")
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
@click.option(
    "-o",
    "--output",
    "output",
    help="output format",
    required=False,
    type=click.Choice(["table", "yaml", "json", "plain"]),
    default="table",
)
def ls(ctx, everything, user, new, ack, output, snooze, resolve, high, low, watch, timeout):
    pd = PD(ctx.obj)
    incs = []
    status = ["triggered"]
    urgencies = ["high", "low"]
    if high:
        urgencies = ["high"]
    if low:
        urgencies = ["low"]

    if not new:
        status.append("acknowledged")

    console = Console()

    userid = None
    if user:
        userid = pd.get_userID_by_name(user)

    while True:

        if everything or userid:
            incs = pd.list_incidents(userid, statuses=status, urgencies=urgencies)
        else:
            incs = pd.list_my_incidents(statuses=status, urgencies=urgencies)

        # Updates
        if len(incs) > 0:
            for i in incs:
                if snooze:
                    print(f"Snoozing incident {i['id']} for 4h")
                    i = pd.snooze(i)

                if resolve:
                    i = pd.resolve(i)
                    print(f"Mark {i['id']} as [green]RESOLVED[/green]")

                if ack:
                    i = pd.ack(i)
                    print(f"Mark {i['id']} as [yellow]ACK[/yellow]")

            if ack or resolve:
                print("Sending bulk updates")
                update = pd.bulk_update_incident(incs)
                print(f"[green]ACK for {len(update)} incidents[green]")

        else:
            if output not in ["yaml", "json"]:
                print("[green]:red_heart-emoji:  Hooray :red_heart-emoji:  No alerts found![/green]")

        # Build filtered list for output
        filtered = [
            {
                "id": i["id"],
                "assignee": [a["assignee"]["summary"] for a in i["assignments"]],
                "urgency": i["urgency"],
                "title": i["title"],
                "url": i["html_url"],
                "status": i["status"],
                "pending_actions": [f"{a['type']} at {a['at']}" for a in i["pending_actions"]],
                "created_at": i["created_at"],
            }
            for i in incs
        ]

        # OUTPUT
        if output == "plain":
            for i in filtered:
                urgency_c = "cyan"
                if i["urgency"] == "high":
                    urgency_c = "red"
                status_c = "green"
                if i["status"] == "triggered":
                    status_c = "red"
                print(
                    f"[magenta]{i['assignee']}[/magenta] [{status_c}]{i['status']}[/{status_c}] [{urgency_c}]{i['title']}[/{urgency_c}]  {i['url']}"
                )
        elif output == "yaml":
            print(yaml.safe_dump(filtered))
        elif output == "json":
            print(json.dumps(filtered))
        elif output == "table" and len(filtered) > 0:
            print(f"[yellow]Found {len(incs)} incidents[/yellow]")
            table = Table(show_header=True, header_style="bold magenta")
            for k, _ in filtered[0].items():
                table.add_column(k)

            with Live(table, refresh_per_second=4):
                for i in filtered:
                    urgency_c = "cyan"
                    if i["urgency"] == "high":
                        urgency_c = "red"
                    status_c = "yellow"
                    if i["status"] == "triggered":
                        status_c = "red"
                    table.add_row(
                        i["id"],
                        f"[magenta]{i['assignee']}[/magenta]",
                        f"[{urgency_c}]{i['urgency']}[/{urgency_c}]",
                        f"[{urgency_c}]{i['title']}[/{urgency_c}]",
                        f"[{urgency_c}]{i['url']}[/{urgency_c}]",
                        f"[{status_c}]{i['status']}[/{status_c}]",
                        "\n".join(i["pending_actions"]),
                        i["created_at"],
                    )
        if not watch:
            break
        time.sleep(timeout)
        console.clear()
