import click
import pkg_resources
import yaml
import json
import os
import sys
from rich import print
from rich.live import Live
from rich.table import Table
from rich.console import Console
from .pd import PD
import time

VERSION = pkg_resources.get_distribution("pdh").version


@click.group()
def main():
    pass


@main.command(help="Create default configuration file")
@click.option(
    "-c",
    "--config",
    default="./pdh.yaml",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        readable=True,
        writable=True,
    ),
    help="Configuration file location (default: ~/.config/pdh.yaml)",
)
def config(config):
    path = os.path.expanduser(config)
    with open(path, "w") as f:
        cfg = {}
        cfg["apikey"] = input("Add Pagerduty API_KEY: ")
        cfg["uid"] = input("Add Pagerduty UserID: ")
        cfg["email"] = input("Add Pagerduty email: ")
        yaml.safe_dump(cfg, f)


@main.group(help="Pagerduty comands")
@click.option(
    "-c",
    "--config",
    envvar="PDH_CONFIG",
    default="./pdh.yaml",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        readable=True,
        writable=True,
    ),
    help="Configuration file location (default: ~/.config/pdh.yaml)",
)
@click.pass_context
def pd(ctx, config):
    cfg = None
    try:
        with open(os.path.expandvars(config), "r") as f:
            cfg = yaml.safe_load(f.read())
        ctx.ensure_object(dict)
        ctx.obj = cfg
    except FileNotFoundError as e:
        print(f"[red]{e}[/red]")
        sys.exit(1)


@main.command(help="Print cloud tools version and exit")
def version():
    click.echo(f"v{VERSION}")


@pd.command(help="List incidents")
@click.pass_context
@click.option("-m", "--mine", help="Filter only mine incidents", is_flag=True, default=False)
@click.option("-u", "--user", default=None, help="Filter only incidents assigned to this user ID")
@click.option("-n", "--new", is_flag=True, default=False, help="Filter only newly triggered incident")
@click.option("-a", "--ack", is_flag=True, default=False, help="Acknowledge incident listed here")
@click.option("-s", "--snooze", is_flag=True, default=False, help="Snooze for 4 hours incident listed here")
@click.option("-r", "--resolve", is_flag=True, default=False, help="Resolve the incident listed here")
@click.option(
    "-o",
    "--output",
    "output",
    help="output format",
    required=False,
    type=click.Choice(["table", "yaml", "json", "plain"]),
    default="table",
)
def ls(ctx, mine, user, new, ack, output, snooze, resolve):
    pd = PD(ctx.obj)
    incs = []
    status = ["triggered"]

    if not new:
        status.append("acknowledged")

    if mine:
        incs = pd.list_my_incidents(statuses=status)
    else:
        incs = pd.list_incidents(user, statuses=status)

    print(f"[yellow]Found {len(incs)} incidents[/yellow]")

    filtered = [
        {
            "id": i["id"],
            "assignee": pd.get_user_names(i),
            "urgency": i["urgency"],
            "title": i["title"],
            "url": i["html_url"],
            "status": i["status"],
            "pending_actions": [f"{a['type']} at {a['at']}" for a in i["pending_actions"]],
            "created_at": i["created_at"],
        }
        for i in incs
    ]

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
    elif output == "table":
        console = Console()
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
    if len(incs) > 0:
        for i in incs:
            if snooze and i["status"] == "acknowledged":
                print(f"Snoozing incident {i['id']} for 4h")
                pd.session.post(f"/incidents/{i['id']}/snooze", json={"duration": 14400})

            if resolve and i["status"] == "acknowledged":
                i["status"] = "resolved"
                print(f"Mark {i['id']} as [green]RESOLVED[/green]")

            if ack and i["status"] != "acknowledged":
                i["status"] = "acknowledged"
                print(f"Mark {i['id']} as [yellow]ACK[/yellow]")

        if ack or resolve:
            print("Sending bulk updates")
            update = pd.session.rput("incidents", json=incs)
            print(f"[green]ACK for {len(update)} incidents[green]")

    else:
        print(f"[green]:red_heart-emoji: Hooray :red_heart-emoji: No alerts found![/green]")
