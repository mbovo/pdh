import click
import pkg_resources
import yaml
import json
import os
import sys
from rich import print
from rich.table import Table
from rich.console import Console
from .pd import PD

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
    default="plain",
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
    if output == "table":
        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        for k in ["assignee", "urgency", "title", "url", "status", "pending_action"]:
            table.add_column(k)
    if len(incs) > 0:
        for i in incs:
            assignee = pd.get_user_names(i)
            pending_actions = "\n".join([f"{a['type']} at {a['at']}" for a in i["pending_actions"]])
            urgency = "cyan"
            if i["urgency"] == "high":
                urgency = "red"
            status = "green"
            if i["status"] == "triggered":
                status = "red"
            if output == "plain":
                print(f"[green]{assignee}[/green]  [{urgency}]{i['title']}[/{urgency}] {i['html_url']}")
            elif output == "yaml":
                print(
                    yaml.safe_dump(
                        {"assignee": assignee, "urgency": i["urgency"], "title": i["title"], "url": i["url"]}
                    )
                )
            elif output == "json":
                print(json.dumps({"assignee": assignee, "urgency": i["urgency"], "title": i["title"], "url": i["url"]}))
            elif output == "table":
                table.add_row(
                    f"[green]{assignee}[/green]",
                    f"[{urgency}]{i['urgency']}[/{urgency}]",
                    f"[{urgency}]{i['title']}[/{urgency}]",
                    f"[{urgency}]{i['html_url']}[/{urgency}]",
                    f"[{status}]{i['status']}[/{status}]",
                    pending_actions,
                )

            if snooze and i["status"] == "acknowledged":
                pd.session.post(f"/incidents/{i['id']}/snooze", json={"duration": 14400})

            if resolve and i["status"] == "acknowledged":
                i["status"] = "resolved"

            if ack and i["status"] != "acknowledged":
                i["status"] = "acknowledged"

        if output == "table":
            console.print(table)
        if ack or resolve:
            update = pd.session.rput("incidents", json=incs)
            print(f"[green]ACK for {len(update)} incidents[green]")

    else:
        print(f"[green]:red_heart-emoji: Hooray :red_heart-emoji: No alerts found![/green]")
