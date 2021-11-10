from typing import Any
import yaml
import os
import sys
import json
from rich import print

REQUIRED_KEYS = ["apikey", "uid", "email"]


class Config(object):
    cfg = {}

    def __init__(self) -> None:
        super().__init__()
        self.cfg = {}

    def from_yaml(self, path, key: str = None) -> None:
        """Load configuration from a yaml file, store it directly or under the specified key (if any)"""

        with open(os.path.expanduser(path), "r") as f:
            o = yaml.safe_load(f.read())
        if key:
            self.cfg[key] = o
        else:
            self.cfg.update(o)

    def to_yaml(self, fileName: str) -> None:
        with open(os.path.expanduser(fileName), "w") as f:
            yaml.safe_dump(self.cfg, f)

    def to_json(self, fileName: str) -> None:
        with open(os.path.expanduser(fileName), "w") as f:
            json.dump(self.cfg, f)

    def from_json(self, path, key: str = None) -> None:
        """Load configuration from a json file, store it directly or under the specified key (if any)"""
        with open(os.path.expanduser(path), "r") as f:
            o = json.load(f)

        if key:
            self.cfg[key] = o
        else:
            self.cfg.update(o)

    def validate(self) -> bool:
        for k in REQUIRED_KEYS:
            if k not in self.cfg.keys():
                return False
        return True

    def __getitem__(self, key: str) -> Any:
        return self.cfg[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.cfg[key] = value

    def __repr__(self) -> str:
        return repr(self.cfg)

    def __str__(self) -> str:
        return repr(self.cfg)

    def __contains__(self, key):
        return key in self.cfg


config = Config()


def load_and_validate(fileName: str) -> dict:
    config.from_yaml(fileName)
    if not config.validate():
        print("[red]Invalid or missing config, try pdh config[/red]")
        sys.exit(1)
    return config


def setup_config(fileName: str) -> None:
    print("Setup [green]PDH[/green]:")
    for k in REQUIRED_KEYS:
        print(f"Add Pagerduty {k}:")
        config[k] = input(":>")
    config.to_yaml(fileName)
