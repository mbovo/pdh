from rich.table import Table

from textual import events
from textual.app import App
from textual.widgets import ScrollView

from .config import load_and_validate
from .pd import (
    DEFAULT_STATUSES,
    DEFAULT_URGENCIES,
    URGENCY_LOW,
    Incidents,
    URGENCY_HIGH,
    STATUS_TRIGGERED,
    STATUS_RESOLVED,
)


EVERYTHING = True
STATUSES = DEFAULT_STATUSES
URGENCIES = DEFAULT_URGENCIES


def build_table() -> Table:

    cfg = load_and_validate("~/.config/pdh.yaml")
    pd = Incidents(cfg)
    if EVERYTHING:
        incs = pd.list(statuses=STATUSES, urgencies=URGENCIES)
    else:
        incs = pd.mine()
    items = [
        {
            "id": i["id"],
            "assignee": f'[magenta]{str([a["assignee"]["summary"] for a in i["assignments"]])}[/magenta]',
            "urgency": f'[red]{i["urgency"]}[/red]' if i["urgency"] == URGENCY_HIGH else f'[cyan]{i["urgency"]}[/cyan]',
            "title": f'[red]{i["title"]}[/red]' if i["urgency"] == URGENCY_HIGH else f'[cyan]{i["title"]}[/cyan]',
            "url": i["html_url"],
            "status": f'[red]{i["status"]}[/red]'
            if i["status"] == STATUS_TRIGGERED
            else f'[green]{i["status"]}[/green]'
            if i["status"] == STATUS_RESOLVED
            else f'[yellow]{i["status"]}[/yellow]',
            "pending_actions": str([f"{a['type']} at {a['at']}" for a in i["pending_actions"]]),
            "created_at": i["created_at"],
        }
        for i in incs
    ]

    skip_columns = []

    table = Table(show_header=True, header_style="bold magenta")
    if len(items) > 0:
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
    else:
        table.add_column("Empty list")
        table.add_row("❤️  Hooray ❤️  No alerts found!")
    return table


class MyApp(App):
    async def on_load(self, event: events.Load) -> None:
        await self.bind("q", "quit", "Quit")
        await self.bind("e", "toggle_everything")
        await self.bind("a", "toggle_high")
        await self.bind("l", "toggle_low")

    async def on_mount(self, event: events.Mount) -> None:

        self.body = body = ScrollView(auto_width=False)
        await self.view.dock(body)

        async def add_content():
            await body.update(build_table())

        self.set_interval(2, add_content)

        await self.call_later(add_content)

    async def action_toggle_everything(self):
        global EVERYTHING
        EVERYTHING = not EVERYTHING

    async def action_toggle_high(self):
        global URGENCIES
        if URGENCY_HIGH in URGENCIES:
            URGENCIES.remove(URGENCY_HIGH)
        else:
            URGENCIES.append(URGENCY_HIGH)

    async def action_toggle_low(self):
        global URGENCIES
        if URGENCY_LOW in URGENCIES:
            URGENCIES.remove(URGENCY_LOW)
        else:
            URGENCIES.append(URGENCY_LOW)
