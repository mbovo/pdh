#
# This file is part of the pdh (https://github.com/mbovo/pdh).
# Copyright (c) 2020-2023 Manuel Bovo.
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
import click
import importlib.metadata
import sys
import re
import os
import time
from rich import print
from rich.console import Console
from .core import PDH

from .pd import Users, Incidents
from .pd import (
    STATUS_TRIGGERED,
    STATUS_ACK,
    URGENCY_HIGH,
    URGENCY_LOW,
    DEFAULT_URGENCIES,
)
from .transformations import Transformation
from .filters import Filter
from .config import load_and_validate, setup_config
from .output import print_items, VALID_OUTPUTS


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
    click.echo(f"v{importlib.metadata.version('pdh')}")


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
@click.option(
    "-f",
    "--fields",
    "fields",
    help="Filter fields",
    required=False,
    type=str,
    default=None,
)
def user_list(ctx, output, fields):
    if not PDH.list_user(ctx.obj, output, fields):
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
@click.option(
    "-f",
    "--fields",
    "fields",
    help="Filter fields",
    required=False,
    type=str,
    default=None,
)
def user_get(ctx, user, output, fields):
    if not PDH.get_user(ctx.obj, user, output, fields):
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
    PDH.ack(ctx.obj, incidentids)


@inc.command(help="Resolve specific incidents IDs")
@click.pass_context
@click.argument("incidentids", nargs=-1)
def resolve(ctx, incidentids):
    PDH.resolve(ctx.obj, incidentids)


@inc.command(help="Snooze the incident(s) for the specified duration in seconds")
@click.pass_context
@click.option("-d", "--duration", required=False, default=14400, help="Duration of snooze in seconds")
@click.argument("incidentids", nargs=-1)
def snooze(ctx, incidentids, duration):
    PDH.snooze(ctx.obj, incidentids, duration)


@inc.command(help="Re-assign the incident(s) to the specified user")
@click.pass_context
@click.option("-u", "--user", required=True, help="User name or email to assign to (fuzzy find!)")
@click.argument("incident", nargs=-1)
def reassign(ctx, incident, user):
    PDH.reassign(ctx.obj, incident, user)


@inc.command(help="Apply scripts with sideeffects to given incident")
@click.pass_context
@click.option("-p", "--path", required=False, default=None, help="Subdirectory with scripts to run")
@click.option("-s", "--script", required=False, default=None, multiple=True, help="Single script to run")
@click.argument("incident", nargs=-1)
@click.option(
    "-o",
    "--output",
    "output",
    help="output format",
    required=False,
    type=click.Choice(VALID_OUTPUTS),
    default="table",
)
def apply(ctx, incident, path, output, script):
    pd = Incidents(ctx.obj)
    incs = pd.list()
    if incident:
        incs = Filter.do(incs, filters=[Filter.inList("id", incident)])

    # load the given parameters
    scripts = script
    # or cycle on every executable found in the given path
    if path is not None:
        scripts = []
        for root, _, filenames in os.walk(os.path.expanduser(os.path.expandvars(path))):
            scripts = [os.path.join(root, fname) for fname in filenames if os.access(os.path.join(root, fname), os.X_OK)]

    ret = pd.apply(incs, scripts)
    for rule in ret:
        print("[green]Applied rule:[/green]", rule["script"])
        if "error" in rule:
            print("[red]Error:[/red]", rule["error"])
        else:
            if type(rule["output"]) is not str:
                print_items(rule["output"], output)
            else:
                print(rule["output"])

    pass


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
@click.option("--apply", is_flag=True, default=False, help="apply rules from a path (see --rules--path")
@click.option("--rules-path", required=False, default="~/.config/pdh_rules", help="Apply all executable find in this path")
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
@click.option("-f", "--fields", "fields", required=False, help="Fields to filter and output", default=None)
@click.option("--alerts", "alerts", required=False, help="Show alerts associated to each incidents", is_flag=True, default=False)
@click.option("--alert-fields", "alert_fields", required=False, help="Show these alert fields only, comma separated", default=None)
@click.option("-S","--service-re", "service_re", required=False, help="Show only incidents for this service (regexp)", default=None)
@click.option("--excluded-service-re", "excluded_service_re", required=False, help="Exclude incident of these services (regexp)", default=None)
def inc_list(ctx, everything, user, new, ack, output, snooze, resolve, high, low, watch, timeout, regexp, apply, rules_path, fields, alerts, alert_fields, service_re, excluded_service_re):

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
    # fallback to configured userid

    # set fields that will be displayed
    if type(fields) is str:
        fields = fields.lower().strip().split(",")
    else:
        fields = ["id", "assignee", "title", "status", "created_at", "last_status_change_at", "url"]
    if alerts:
        fields.append("alerts")

    if type(alert_fields) is str:
        alert_fields = alert_fields.lower().strip().split(",")
    else:
        alert_fields = ["status", "created_at", "service.summary", "body.details.Condition", "body.details.Segment", "body.details.Scope"]

    if not everything and not userid:
        userid = pd.cfg["uid"]
    while True:
        incs = pd.list(userid, statuses=status, urgencies=urgencies)
        # BUGFIX: filter by regexp must be applyed to the original list, not only to the transformed one
        incs = Filter.do(incs, filters=[Filter.regexp("title", filter_re)])

        if service_re:
            incs = Filter.do(incs, transformations={"service": Transformation.extract_from_dict("service","summary")}, filters=[Filter.regexp("service", service_re)], preserve=True)

        if excluded_service_re:
            incs = Filter.do(incs, transformations={"service": Transformation.extract_from_dict("service","summary")}, filters=[Filter.not_regexp("service", excluded_service_re)], preserve=True)

        if alerts:
            for i in incs:
                i["alerts"] = pd.alerts(i["id"])

        # Build filtered list for output
        if output != "raw":
            transformations = dict()
            for f in fields:
                transformations[f] = Transformation.extract_field(f)
                # special cases
                if f == "assignee":
                    transformations[f] = Transformation.extract_assignees()
                if f == "status":
                    transformations[f] = Transformation.extract_field("status", ["red", "yellow"], "status", STATUS_TRIGGERED, True, {STATUS_ACK: "✔", STATUS_TRIGGERED: "✘"})
                if f == "url":
                    transformations[f] = Transformation.extract_field("html_url")
                if f in ["title", "urgency"]:
                    transformations[f] = Transformation.extract_field(f, check=True)
                if f in ["created_at", "last_status_change_at"]:
                    transformations[f] = Transformation.extract_date(f)
                if f in ["alerts"]:
                    transformations[f] = Transformation.extract_alerts(f, alert_fields)

            filtered = Filter.do(incs, transformations)
        else:
            # raw output, using json format
            filtered = incs

        # define here how print in "plain" way (ie if output=plain)
        def plain_print_f(i):
            s = ""
            for f in fields:
                s += f"{i[f]}\t"
            print(s)

        print_items(filtered, output, plain_print_f=plain_print_f)

        # now apply actions like snooze, resolve, ack...
        ids = [i["id"] for i in incs]
        if ack:
            pd.ack(incs)
            if output not in ["yaml", "json"]:
                for i in ids:
                    print(f"Marked {i} as [yellow]ACK[/yellow]")
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
        if apply:
            scripts = []
            ppath = os.path.expanduser(os.path.expandvars(rules_path))
            for root, _, filenames in os.walk(ppath):
                for filename in filenames:
                    fullpath = os.path.join(root, filename)
                    if os.access(fullpath, os.X_OK):
                        scripts.append(fullpath)

            if len(scripts) == 0:
                print(f"[yellow]No rules found in {ppath}[/yellow]")
            ret = pd.apply(incs, scripts)
            for rule in ret:
                print("[green]Applied rule:[/green]", rule["script"])
                if "error" in rule:
                    print("[red]Error:[/red]", rule["error"])
                else:
                    if type(rule["output"]) is not str:
                        print_items(rule["output"], output)
                    else:
                        print(rule["output"])

        if not watch:
            break
        time.sleep(timeout)
        console.clear()
