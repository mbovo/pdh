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
import yaml
import json
from rich.table import Table
from rich.console import Console
from rich import print as rich_print

VALID_OUTPUTS = ["plain", "table", "json", "yaml", "raw"]


class Output(object):
    def plain(self, **kwargs) -> None:
        items = kwargs["items"] if "items" in kwargs else []
        plain_print_f = kwargs["print_f"] if "print_f" in kwargs else None
        console = kwargs["console"] if "console" in kwargs else Console()
        for i in items:
            if plain_print_f:
                plain_print_f(i)
            else:
                console.print(i)

    def raw(self, **kwargs) -> None:
        items = kwargs["items"] if "items" in kwargs else []
        console = kwargs["console"] if "console" in kwargs else Console()
        console.print(items)

    def yaml(self, **kwargs) -> None:
        items = kwargs["items"] if "items" in kwargs else []
        console = kwargs["console"] if "console" in kwargs else Console()
        console.print(yaml.safe_dump(items))

    def json(self, **kwargs) -> None:
        items = kwargs["items"] if "items" in kwargs else []
        console = kwargs["console"] if "console" in kwargs else Console()
        console.print(json.dumps(items))

    def table(self, **kwargs) -> None:
        items = kwargs["items"] if "items" in kwargs else []
        console = kwargs["console"] if "console" in kwargs else Console()
        skip_columns = kwargs["skip_columns"] if "skip_columns" in kwargs else []
        odd_color = kwargs["odd_color"] if "odd_color" in kwargs else "grey93 on black"
        even_color = kwargs["even_color"] if "even_color" in kwargs else "grey50 on black"

        if len(items) > 0:
            t = Table(show_header=True, header_style="bold magenta")
            for k, _ in items[0].items():
                if k not in skip_columns:
                    t.add_column(k)
            i = 0
            for u in items:
                args = [v for k, v in u.items() if k not in skip_columns]
                if i % 2:
                    t.add_row(*args, style=odd_color)
                else:
                    t.add_row(*args, style=even_color)
                i += 1
            console.print(t)


def print_items(
    items, output, skip_columns: list = [], plain_print_f=None, console: Console = Console(), odd_color: str = "grey93 on black", even_color: str = "grey50 on black"
) -> None:
    getattr(Output(), output)(items=items, skip_columns=skip_columns, print_f=plain_print_f, console=console, odd_color=odd_color, even_color=even_color)


def print(*args, **kwargs):
    rich_print(*args, **kwargs)
