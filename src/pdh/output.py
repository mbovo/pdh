from typing import Any
import yaml
import json
from rich.table import Table
from rich.console import Console
from rich import print as rich_print

VALID_OUTPUTS = ["plain", "table", "json", "yaml", "raw"]


class Output(object):
    def plain(
        items: list, skip_columns: list = [], plain_print_f=None, console: Console = Console(), odd_color: str = "grey93 on black", even_color: str = "grey50 on black"
    ) -> None:
        for i in items:
            if plain_print_f:
                plain_print_f(i)
            else:
                console.print(i)

    def raw(
        items: list, skip_columns: list = [], plain_print_f=None, console: Console = Console(), odd_color: str = "grey93 on black", even_color: str = "grey50 on black"
    ) -> None:
        console.print(items)

    def yaml(
        items: list, skip_columns: list = [], plain_print_f=None, console: Console = Console(), odd_color: str = "grey93 on black", even_color: str = "grey50 on black"
    ) -> None:
        console.print(yaml.safe_dump(items))

    def json(
        items: list, skip_columns: list = [], plain_print_f=None, console: Console = Console(), odd_color: str = "grey93 on black", even_color: str = "grey50 on black"
    ) -> None:
        console.print(json.dumps(items))

    def table(items: list, skip_columns: list = [], console: Console = Console(), odd_color: str = "grey93 on black", even_color: str = "grey50 on black") -> None:
        if len(items) > 0:
            table = Table(show_header=True, header_style="bold magenta")
            for k, _ in items[0].items():
                if k not in skip_columns:
                    table.add_column(k)
            i = 0
            for u in items:
                args = [v for k, v in u.items() if k not in skip_columns]
                if i % 2:
                    table.add_row(*args, style=odd_color)
                else:
                    table.add_row(*args, style=even_color)
                i += 1
            console.print(table)


def print_items(
    items, output, skip_columns: list = [], plain_print_f=None, console: Console = Console(), odd_color: str = "grey93 on black", even_color: str = "grey50 on black"
) -> None:
    out = Output()
    m = getattr(out, output)
    m(items, skip_columns, plain_print_f, console, odd_color, even_color)


def print(*args, **kwargs):
    rich_print(*args, **kwargs)
